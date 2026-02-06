"""
Sistema de Aprendizado Contínuo para LLM
=========================================

Implementa Online Feedback Loop moderno (2025) que transforma feedback passivo
em melhoria ativa do modelo através de:
- Coleta inteligente de feedback
- Golden dataset curation
- Prompt re-optimization automática
- Low-confidence routing para supervisão humana

Author: Agent BI Team
Date: 2025-12-27
"""

import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from collections import defaultdict

from app.config.settings import settings

logger = logging.getLogger(__name__)


class ContinuousLearner:
    """
    Sistema de aprendizado contínuo que processa feedback do usuário
    e automaticamente melhora a qualidade das respostas.

    Inspirado em: Lemma (YC 2025) e best practices de LLMOps 2025
    """

    def __init__(
        self,
        golden_dataset_path: str = None,
        feedback_buffer_size: int = 100,
        confidence_threshold: float = 0.7,
        auto_optimize: bool = True
    ):
        """
        Inicializa o Continuous Learner.

        Args:
            golden_dataset_path: Caminho para armazenar golden dataset
            feedback_buffer_size: Tamanho do buffer antes de re-otimizar
            confidence_threshold: Threshold para routing humano (< 0.7 = baixa confiança)
            auto_optimize: Se True, re-otimiza prompts automaticamente
        """
        self.golden_dataset_path = golden_dataset_path or str(Path(settings.LEARNING_EXAMPLES_PATH) / "golden_dataset")
        self.feedback_buffer_size = feedback_buffer_size
        self.confidence_threshold = confidence_threshold
        self.auto_optimize = auto_optimize

        # Buffers em memória
        self.feedback_buffer: List[Dict[str, Any]] = []
        self.pending_review: List[Dict[str, Any]] = []

        # Estatísticas
        self.stats = {
            'total_processed': 0,
            'positive_count': 0,
            'negative_count': 0,
            'partial_count': 0,
            'low_confidence_count': 0,
            'optimizations_triggered': 0
        }

        # Criar diretórios
        os.makedirs(self.golden_dataset_path, exist_ok=True)
        os.makedirs(os.path.join(self.golden_dataset_path, "positive"), exist_ok=True)
        os.makedirs(os.path.join(self.golden_dataset_path, "review"), exist_ok=True)

        logger.info(f"ContinuousLearner inicializado: golden_dataset={self.golden_dataset_path}")

    async def process_interaction(
        self,
        query: str,
        response: Dict[str, Any],
        feedback_type: Optional[str] = None,
        user_comment: Optional[str] = None,
        confidence_score: Optional[float] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processa uma interação completa (query + response + feedback).

        Este é o coração do continuous learning loop:
        1. Armazena feedback
        2. Se positivo → golden dataset
        3. Se negativo → review queue
        4. Se baixa confiança → routing humano
        5. Trigger re-optimization quando buffer cheio

        Args:
            query: Query original do usuário
            response: Resposta gerada pelo agente
            feedback_type: 'positive', 'negative', 'partial', ou None (sem feedback ainda)
            user_comment: Comentário opcional do usuário
            confidence_score: Score de confiança (0.0-1.0)
            session_id: ID da sessão
            user_id: ID do usuário

        Returns:
            Dict com ações tomadas e recomendações
        """
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'response': response,
            'feedback_type': feedback_type,
            'user_comment': user_comment,
            'confidence_score': confidence_score,
            'session_id': session_id,
            'user_id': user_id
        }

        actions_taken = []
        recommendations = []

        # Estatísticas
        self.stats['total_processed'] += 1

        # 1. Processar feedback se disponível
        if feedback_type:
            if feedback_type == 'positive':
                self.stats['positive_count'] += 1
                await self._add_to_golden_dataset(interaction)
                actions_taken.append("added_to_golden_dataset")

            elif feedback_type == 'negative':
                self.stats['negative_count'] += 1
                await self._flag_for_human_review(interaction)
                actions_taken.append("flagged_for_review")
                recommendations.append("Revisar manualmente para identificar padrão de erro")

            elif feedback_type == 'partial':
                self.stats['partial_count'] += 1

        # 2. Verificar confiança
        if confidence_score is not None and confidence_score < self.confidence_threshold:
            self.stats['low_confidence_count'] += 1
            await self._flag_for_human_review(interaction)
            actions_taken.append("low_confidence_routing")
            recommendations.append(f"Confiança baixa ({confidence_score:.2f}). Requer validação humana.")

        # 3. Adicionar ao buffer
        self.feedback_buffer.append(interaction)

        # 4. Trigger re-optimization se buffer cheio
        if len(self.feedback_buffer) >= self.feedback_buffer_size and self.auto_optimize:
            optimization_result = await self._trigger_prompt_optimization()
            actions_taken.append("triggered_optimization")
            self.stats['optimizations_triggered'] += 1
            recommendations.append(f"Otimização automática executada: {optimization_result}")

        return {
            'actions_taken': actions_taken,
            'recommendations': recommendations,
            'stats': self.stats.copy()
        }

    async def _add_to_golden_dataset(self, interaction: Dict[str, Any]) -> bool:
        """
        Adiciona uma interação bem-sucedida ao golden dataset.

        Golden dataset é usado para:
        - Few-shot examples em prompts
        - Fine-tuning (se disponível)
        - RAG context para queries similares
        """
        try:
            # Gerar filename único baseado em timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"golden_{timestamp}.json"
            filepath = os.path.join(self.golden_dataset_path, "positive", filename)

            # Extrair informações relevantes
            golden_entry = {
                'timestamp': interaction['timestamp'],
                'query': interaction['query'],
                'response': interaction['response'],
                'user_id': interaction.get('user_id'),
                'confidence_score': interaction.get('confidence_score'),
                'tags': self._extract_tags(interaction['query'])  # Auto-tagging
            }

            # Salvar
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(golden_entry, f, indent=2, ensure_ascii=False)

            logger.info(f"Golden dataset entry criado: {filename}")
            return True

        except Exception as e:
            logger.error(f"Erro ao adicionar ao golden dataset: {e}")
            return False

    async def _flag_for_human_review(self, interaction: Dict[str, Any]) -> bool:
        """
        Marca interação para review humano.

        Casos:
        - Feedback negativo
        - Baixa confiança (< threshold)
        - Padrões incomuns
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"review_{timestamp}.json"
            filepath = os.path.join(self.golden_dataset_path, "review", filename)

            review_entry = {
                'timestamp': interaction['timestamp'],
                'query': interaction['query'],
                'response': interaction['response'],
                'feedback_type': interaction.get('feedback_type'),
                'user_comment': interaction.get('user_comment'),
                'confidence_score': interaction.get('confidence_score'),
                'review_status': 'pending',
                'priority': self._calculate_review_priority(interaction)
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(review_entry, f, indent=2, ensure_ascii=False)

            self.pending_review.append(review_entry)
            logger.warning(f"Interação marcada para review: {filename} (priority={review_entry['priority']})")
            return True

        except Exception as e:
            logger.error(f"Erro ao marcar para review: {e}")
            return False

    def _calculate_review_priority(self, interaction: Dict[str, Any]) -> str:
        """
        Calcula prioridade de review (high/medium/low).

        High priority:
        - Confiança < 0.5
        - Feedback negativo com comentário
        - Erro detectado
        """
        confidence = interaction.get('confidence_score', 1.0)
        feedback = interaction.get('feedback_type')
        has_comment = bool(interaction.get('user_comment'))

        if confidence < 0.5:
            return 'high'
        if feedback == 'negative' and has_comment:
            return 'high'
        if feedback == 'negative':
            return 'medium'
        if confidence < 0.7:
            return 'medium'

        return 'low'

    async def _trigger_prompt_optimization(self) -> str:
        """
        Analisa feedback buffer e sugere otimizações de prompt.

        Estratégias:
        1. Identificar padrões de erro comuns
        2. Extrair exemplos positivos para few-shot
        3. Sugerir ajustes no system prompt

        Returns:
            Descrição das otimizações sugeridas
        """
        try:
            logger.info(f"Iniciando otimização de prompts (buffer size={len(self.feedback_buffer)})")

            # Analisar feedback buffer
            positive_examples = [
                fb for fb in self.feedback_buffer
                if fb.get('feedback_type') == 'positive'
            ]
            negative_examples = [
                fb for fb in self.feedback_buffer
                if fb.get('feedback_type') == 'negative'
            ]

            # Identificar padrões de erro
            error_patterns = self._identify_error_patterns(negative_examples)

            # Selecionar melhores few-shot examples
            best_examples = self._select_best_few_shot_examples(positive_examples, top_k=5)

            # Gerar relatório de otimização
            optimization_report = {
                'timestamp': datetime.now().isoformat(),
                'buffer_size': len(self.feedback_buffer),
                'positive_count': len(positive_examples),
                'negative_count': len(negative_examples),
                'error_patterns': error_patterns,
                'recommended_few_shot_examples': best_examples,
                'suggestions': self._generate_optimization_suggestions(error_patterns)
            }

            # Salvar relatório
            report_path = os.path.join(self.golden_dataset_path, f"optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(optimization_report, f, indent=2, ensure_ascii=False)

            # Limpar buffer
            self.feedback_buffer.clear()

            logger.info(f"Otimização completa. Relatório salvo: {report_path}")
            return f"Identificados {len(error_patterns)} padrões de erro, {len(best_examples)} exemplos recomendados"

        except Exception as e:
            logger.error(f"Erro na otimização de prompts: {e}")
            return f"Erro: {str(e)}"

    def _identify_error_patterns(self, negative_examples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identifica padrões comuns em feedback negativo.

        Analisa:
        - Keywords frequentes em queries problemáticas
        - Tipos de erro comuns
        - Comentários dos usuários
        """
        if not negative_examples:
            return []

        # Agrupar por comentários similares
        patterns = defaultdict(list)

        for example in negative_examples:
            query = example.get('query', '').lower()
            comment = example.get('user_comment', '').lower()

            # Extrair keywords
            keywords = self._extract_keywords(query)

            # Agrupar por keyword principal
            if keywords:
                main_keyword = keywords[0]
                patterns[main_keyword].append({
                    'query': query,
                    'comment': comment
                })

        # Converter para lista de padrões
        error_patterns = []
        for keyword, examples in patterns.items():
            if len(examples) >= 2:  # Mínimo 2 ocorrências para ser um padrão
                error_patterns.append({
                    'keyword': keyword,
                    'occurrences': len(examples),
                    'sample_queries': [ex['query'] for ex in examples[:3]],
                    'sample_comments': [ex['comment'] for ex in examples[:3] if ex['comment']]
                })

        return sorted(error_patterns, key=lambda x: x['occurrences'], reverse=True)

    def _select_best_few_shot_examples(self, positive_examples: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Seleciona os melhores exemplos para few-shot learning.

        Critérios:
        - Alta confiança
        - Queries diversas (evitar duplicatas)
        - Respostas completas
        """
        if not positive_examples:
            return []

        # Ordenar por confiança
        sorted_examples = sorted(
            positive_examples,
            key=lambda x: x.get('confidence_score', 0.5),
            reverse=True
        )

        # Selecionar top_k com diversidade
        selected = []
        seen_keywords = set()

        for example in sorted_examples:
            if len(selected) >= top_k:
                break

            keywords = set(self._extract_keywords(example.get('query', '')))

            # Adicionar se traz keywords novas (diversidade)
            if not keywords.issubset(seen_keywords) or len(selected) < 2:
                selected.append({
                    'query': example.get('query'),
                    'response': example.get('response'),
                    'confidence': example.get('confidence_score')
                })
                seen_keywords.update(keywords)

        return selected

    def _generate_optimization_suggestions(self, error_patterns: List[Dict[str, Any]]) -> List[str]:
        """
        Gera sugestões concretas de otimização baseadas nos padrões de erro.
        """
        suggestions = []

        if not error_patterns:
            suggestions.append("Nenhum padrão de erro identificado. Sistema operando bem!")
            return suggestions

        for pattern in error_patterns[:3]:  # Top 3 padrões
            keyword = pattern['keyword']
            occurrences = pattern['occurrences']

            suggestions.append(
                f"Adicionar exemplo específico para queries com '{keyword}' "
                f"(ocorreu {occurrences}x com feedback negativo)"
            )

        # Sugestões gerais
        if len(error_patterns) > 5:
            suggestions.append("Alta variabilidade de erros. Considerar revisar system prompt base.")

        return suggestions

    def _extract_tags(self, query: str) -> List[str]:
        """
        Extrai tags automáticas de uma query para categorização.

        Exemplos:
        - "vendas por segmento" → ['vendas', 'segmento', 'analise']
        - "estoque crítico" → ['estoque', 'ruptura', 'alerta']
        """
        query_lower = query.lower()
        tags = []

        # Tags baseadas em keywords
        tag_mapping = {
            'vendas': ['venda', 'vendas', 'vendi', 'receita'],
            'estoque': ['estoque', 'inventário', 'ruptura'],
            'transferência': ['transferência', 'transferir', 'mover'],
            'analise': ['análise', 'analisar', 'análise', 'relatorio'],
            'segmento': ['segmento', 'categoria'],
            'produto': ['produto', 'item', 'sku'],
            'une': ['une', 'loja', 'filial'],
        }

        for tag, keywords in tag_mapping.items():
            if any(kw in query_lower for kw in keywords):
                tags.append(tag)

        return tags if tags else ['geral']

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extrai keywords principais de um texto.
        """
        # Stopwords básicas
        stopwords = {'o', 'a', 'de', 'da', 'do', 'em', 'para', 'por', 'com', 'e', 'os', 'as'}

        words = text.lower().split()
        keywords = [w for w in words if w not in stopwords and len(w) > 3]

        return keywords[:5]  # Top 5 keywords

    def get_golden_dataset_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do golden dataset.
        """
        positive_path = os.path.join(self.golden_dataset_path, "positive")
        review_path = os.path.join(self.golden_dataset_path, "review")

        positive_count = len([f for f in os.listdir(positive_path) if f.endswith('.json')]) if os.path.exists(positive_path) else 0
        review_count = len([f for f in os.listdir(review_path) if f.endswith('.json')]) if os.path.exists(review_path) else 0

        return {
            'golden_examples': positive_count,
            'pending_review': review_count,
            'buffer_size': len(self.feedback_buffer),
            'stats': self.stats.copy()
        }

    def get_pending_reviews(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retorna itens pendentes de review humano, ordenados por prioridade.
        """
        review_path = os.path.join(self.golden_dataset_path, "review")

        if not os.path.exists(review_path):
            return []

        reviews = []
        for filename in sorted(os.listdir(review_path), reverse=True):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(review_path, filename), 'r', encoding='utf-8') as f:
                        review = json.load(f)
                        reviews.append(review)
                except Exception as e:
                    logger.error(f"Erro ao ler review {filename}: {e}")

        # Ordenar por prioridade
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        reviews.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 3))

        return reviews[:limit]


# Singleton instance
_continuous_learner: Optional[ContinuousLearner] = None


def get_continuous_learner() -> ContinuousLearner:
    """
    Retorna instância singleton do ContinuousLearner.
    """
    global _continuous_learner
    if _continuous_learner is None:
        _continuous_learner = ContinuousLearner()
    return _continuous_learner
