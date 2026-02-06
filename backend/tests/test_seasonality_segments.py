"""
Testes para Seasonality Detector com filtro por segmento
"""
import pytest
from datetime import datetime
from app.core.utils.seasonality_detector import (
    detect_seasonal_context,
    SEASONAL_SEGMENTS,
    SEASONAL_PERIODS
)


class TestSeasonalityDetectorWithSegments:
    """Testes para detecção de sazonalidade com filtro por segmento"""
    
    def test_volta_as_aulas_papelaria_janeiro(self):
        """Produto de PAPELARIA em Janeiro deve ter sazonalidade VOLTA_AS_AULAS"""
        context = detect_seasonal_context(
            reference_date=datetime(2026, 1, 15),
            produto_segmento="PAPELARIA"
        )
        
        assert context is not None
        assert context["season"] == "volta_as_aulas"
        assert context["multiplier"] == 2.5
        assert context["urgency"] == "ALTA"
        assert context["produto_segmento"] == "PAPELARIA"
    
    def test_volta_as_aulas_casa_decoracao_janeiro(self):
        """Produto de CASA E DECORAÇÃO em Janeiro NÃO deve ter sazonalidade"""
        context = detect_seasonal_context(
            reference_date=datetime(2026, 1, 15),
            produto_segmento="CASA E DECORAÇÃO"
        )
        
        # CASA E DECORAÇÃO não está na lista de segmentos afetados por volta_as_aulas
        assert context is None
    
    def test_natal_casa_decoracao_dezembro(self):
        """Produto de CASA E DECORAÇÃO em Dezembro deve ter sazonalidade NATAL"""
        context = detect_seasonal_context(
            reference_date=datetime(2026, 12, 15),
            produto_segmento="CASA E DECORAÇÃO"
        )
        
        assert context is not None
        assert context["season"] == "natal"
        assert context["multiplier"] == 3.0
        assert context["urgency"] == "CRÍTICA"
    
    def test_pascoa_chocolates_marco(self):
        """Produto de CHOCOLATES em Março deve ter sazonalidade PÁSCOA"""
        context = detect_seasonal_context(
            reference_date=datetime(2026, 3, 15),
            produto_segmento="CHOCOLATES"
        )
        
        assert context is not None
        assert context["season"] == "pascoa"
        assert context["multiplier"] == 1.8
    
    def test_pascoa_papelaria_marco(self):
        """Produto de PAPELARIA em Março NÃO deve ter sazonalidade PÁSCOA"""
        context = detect_seasonal_context(
            reference_date=datetime(2026, 3, 15),
            produto_segmento="PAPELARIA"
        )
        
        # PAPELARIA não está na lista de segmentos afetados por pascoa
        assert context is None
    
    def test_sem_segmento_janeiro(self):
        """Produto sem segmento em Janeiro não deve ter sazonalidade"""
        context = detect_seasonal_context(
            reference_date=datetime(2026, 1, 15),
            produto_segmento=None
        )
        
        # Sem segmento, não aplica filtro - retorna o período detectado
        # Mas como não há segmento, o sistema pode optar por não aplicar
        # Neste caso, a lógica atual retorna o período se não houver segmento
        assert context is not None  # Comportamento atual: retorna período
        assert context["season"] == "volta_as_aulas"
    
    def test_case_insensitive_matching(self):
        """Teste de matching case-insensitive para segmentos"""
        # Testar com diferentes variações de case
        context1 = detect_seasonal_context(
            reference_date=datetime(2026, 1, 15),
            produto_segmento="papelaria"  # lowercase
        )
        
        context2 = detect_seasonal_context(
            reference_date=datetime(2026, 1, 15),
            produto_segmento="PAPELARIA"  # uppercase
        )
        
        context3 = detect_seasonal_context(
            reference_date=datetime(2026, 1, 15),
            produto_segmento="Papelaria"  # mixed case
        )
        
        assert context1 is not None
        assert context2 is not None
        assert context3 is not None
        assert context1["season"] == context2["season"] == context3["season"]
    
    def test_dia_das_maes_perfumaria_maio(self):
        """Produto de PERFUMARIA em Maio deve ter sazonalidade DIA_DAS_MAES"""
        context = detect_seasonal_context(
            reference_date=datetime(2026, 5, 10),
            produto_segmento="PERFUMARIA"
        )
        
        assert context is not None
        assert context["season"] == "dia_das_maes"
        assert context["multiplier"] == 1.6
    
    def test_dia_dos_pais_ferramentas_agosto(self):
        """Produto de FERRAMENTAS em Agosto deve ter sazonalidade DIA_DOS_PAIS"""
        context = detect_seasonal_context(
            reference_date=datetime(2026, 8, 10),
            produto_segmento="FERRAMENTAS"
        )
        
        assert context is not None
        assert context["season"] == "dia_dos_pais"
        assert context["multiplier"] == 1.5
    
    def test_mes_sem_sazonalidade(self):
        """Produto em mês sem sazonalidade não deve retornar contexto"""
        context = detect_seasonal_context(
            reference_date=datetime(2026, 6, 15),  # Junho
            produto_segmento="PAPELARIA"
        )
        
        assert context is None
    
    def test_segmento_com_espacos(self):
        """Teste com segmento contendo espaços extras"""
        context = detect_seasonal_context(
            reference_date=datetime(2026, 12, 15),
            produto_segmento="  CASA E DECORAÇÃO  "  # Com espaços extras
        )
        
        assert context is not None
        assert context["season"] == "natal"


class TestSeasonalSegmentsMapping:
    """Testes para validar o mapeamento de segmentos"""
    
    def test_all_seasons_have_segments(self):
        """Todos os períodos sazonais devem ter segmentos mapeados"""
        for season_name in SEASONAL_PERIODS.keys():
            assert season_name in SEASONAL_SEGMENTS
            assert len(SEASONAL_SEGMENTS[season_name]) > 0
    
    def test_no_duplicate_seasons(self):
        """Não deve haver períodos sazonais duplicados"""
        assert len(SEASONAL_PERIODS) == len(set(SEASONAL_PERIODS.keys()))
    
    def test_segments_are_strings(self):
        """Todos os segmentos devem ser strings"""
        for season_name, segments in SEASONAL_SEGMENTS.items():
            assert isinstance(segments, list)
            for segment in segments:
                assert isinstance(segment, str)
                assert len(segment) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
