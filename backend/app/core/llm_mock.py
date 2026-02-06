from typing import Any, List, Optional
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage
from app.core.llm_langchain_adapter import CustomLangChainLLM

class MockLLM(CustomLangChainLLM):
    """
    Mock LLM para o modo Offline / Arquitetura LangGraph Pura.
    Não faz chamadas de API.
    
    Comportamento:
    1. Se receber output de ferramenta (ToolMessage), formata e retorna ao usuário.
    2. Se receber input do usuário sem heurística prévia, retorna mensagem padrão.
    """
    
    def __init__(self, **kwargs):
        # Inicializa sem adapter real, pois não faremos chamadas
        # hack: passar None ou um dummy para satisfazer o init do pai se necessário
        # mas como sobrescrevemos invoke, talvez não precise
        super().__init__(llm_adapter=None, **kwargs)
        
    def bind_tools(self, tools):
        # Aceita tools mas ignora (quem decide usar tools é a Heurística, não este Mock)
        return self
        
    def invoke(self, messages: List[BaseMessage], **kwargs) -> AIMessage:
        last_msg = messages[-1]
        
        # CASO 1: O Agente recebeu o resultado de uma ferramenta
        if isinstance(last_msg, ToolMessage) or (isinstance(last_msg, dict) and last_msg.get("role") == "tool"):
            tool_output = last_msg.content
            
            # Formatação Inteligente
            formatted_response = self._format_tool_output(tool_output)
            return AIMessage(content=formatted_response)

        # CASO 2: Mensagem de Usuário (Sem Heurística)
        fallback_msg = (
            "No modo **Offline**, eu respondo perguntas objetivas sobre a base de dados.\n\n"
            "Exemplos:\n"
            "- *Qual é o preço do produto 59294?*\n"
            "- *Estoque do produto X na filial Y*\n"
            "- *Gráfico de vendas por grupo*"
        )
        return AIMessage(content=fallback_msg)
    
    def _format_tool_output(self, tool_output: str) -> str:
        """
        Transforma o output JSON da ferramenta em uma resposta natural e bonita.
        """
        import json
        
        # 1. Tentar parsear JSON
        try:
            data = json.loads(tool_output)
        except:
            # Se não for JSON, retorna como está (pode ser erro ou texto simples)
            return tool_output

        # Se for string JSON wrapada em markdown (common in chat history)
        if isinstance(data, str) and data.startswith("```json"):
             return data

        # 2. Verificar se é Gráfico (chart_spec)
        # Se for grafico, retorna o JSON puro envelopado em markdown para o frontend renderizar
        if isinstance(data, dict) and ("chart_spec" in data or "chart_data" in data or "type" == "chart"):
             # Garante que está no formato que o frontend detecta
             return f"```json\n{json.dumps(data, indent=2)}\n```"

        # 3. Verificar Resultados de Dados (flexible_query_tool)
        results = data.get("resultados", []) if isinstance(data, dict) else []
        if not results:
            msg = data.get("mensagem", "Nenhum dado encontrado.") if isinstance(data, dict) else str(data)
            return f"Não encontrei dados para sua consulta.\n\n*Detalhe: {msg}*"

        # 4. Heurística de Intenção baseada nas colunas do primeiro registro
        first_row = results[0]
        keys = set(first_row.keys())
        
        # --- TEMPLATE: PREÇO ---
        if "LIQUIDO_38" in keys and "PRODUTO" in keys:
            # Exibe o primeiro resultado em destaque
            row = first_row
            nome = row.get("NOME", row.get("DESCRIÇÃO", "Produto"))
            codigo = row.get("PRODUTO", row.get("CODIGO", ""))
            preco = float(row.get("LIQUIDO_38", 0))
            estoque = row.get("ESTOQUE_UNE", 0)
            
            response =f"O preço do produto **{nome}** ({codigo}) é **R$ {preco:,.2f}**."
            
            # Adicionar info extra se disponível
            if estoque > 0:
                response += f"\n\n📦 Estoque Atual: **{estoque} unidades**."
            
            response += "\n\n*(Gerado via Arquitetura Local)*"
            return response

        # --- TEMPLATE: ESTOQUE (Múltiplas UNEs ou Geral) ---
        elif "ESTOQUE_UNE" in keys and "UNE" in keys:
             # Soma total
             total_estoque = sum([r.get("ESTOQUE_UNE", 0) for r in results])
             nome = first_row.get("NOME", "Produto")
             codigo = first_row.get("PRODUTO", "")
             
             response = f"O produto **{nome}** ({codigo}) possui um total de **{total_estoque} unidades** em estoque nas filiais consultadas.\n\n"
             
             # Tabela detalhada
             response += "| Filial (UNE) | Quantidade |\n|---|---|\n"
             for r in results[:5]:
                 response += f"| {r.get('UNE')} | {r.get('ESTOQUE_UNE')} |\n"
                 
             if len(results) > 5:
                  response += f"| ... | ... |"
                  
             return response

        # --- TEMPLATE: GENÉRICO (Tabela Markdown) ---
        else:
             # Montar tabela markdown dinâmica
             cols = list(keys)[:4] # Limit to 4 cols for mobile view
             header = "| " + " | ".join(cols) + " |"
             separator = "| " + " | ".join(["---"] * len(cols)) + " |"
             
             rows_md = []
             for r in results[:5]:
                 if not r: continue # Defensive check
                 row_vals = [str(r.get(c, "-")) for c in cols]
                 rows_md.append("| " + " | ".join(row_vals) + " |")
             
             table = "\n".join([header, separator] + rows_md)
             
             count = len(results)
             msg = f"Encontrei **{count} registros** correspondentes:\n\n{table}"
             if count > 5:
                 msg += f"\n\n*(...e mais {count-5} registros)*"
                 
             return msg

    
    async def ainvoke(self, messages: List[BaseMessage], **kwargs) -> AIMessage:
        # Suporte Async simples
        return self.invoke(messages, **kwargs)
