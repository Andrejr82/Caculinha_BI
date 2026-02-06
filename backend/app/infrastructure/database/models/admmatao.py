from sqlalchemy import Column, Integer, String, Float, DateTime, BigInteger
from sqlalchemy.sql import func
from app.config.database import Base

class Admmatao(Base):
    __tablename__ = "admmatao"

    id = Column(BigInteger, primary_key=True, index=True)
    une = Column(BigInteger, index=True)
    produto = Column(BigInteger)
    tipo = Column(BigInteger)
    une_nome = Column(String(255))
    nome = Column(String(255))
    embalagem = Column(String(255))
    nomesegmento = Column(String(255))
    nomecategoria = Column(String(255))
    nomegrupo = Column(String(255))
    nomesubgrupo = Column(String(255))
    nomefabricante = Column(String(255))
    ean = Column(String(50))
    promocional = Column(String(50))
    foralinha = Column(String(50))
    
    # Métricas e Dados Adicionais
    liquido_38 = Column(Float)
    qtde_emb_master = Column(Float)
    qtde_emb_multiplo = Column(Float)
    
    # Curvas ABC
    abc_une_mes_04 = Column(String(10))
    abc_une_mes_03 = Column(String(10))
    abc_une_mes_02 = Column(String(10))
    abc_une_mes_01 = Column(String(10))
    abc_une_30dd = Column(String(10))
    abc_cacula_90dd = Column(String(10))
    abc_une_30xabc_cacula_90dd = Column(String(10))
    
    # Vendas Mensais
    mes_12 = Column(Float)
    mes_11 = Column(Float)
    mes_10 = Column(Float)
    mes_09 = Column(Float)
    mes_08 = Column(Float)
    mes_07 = Column(Float)
    mes_06 = Column(Float)
    mes_05 = Column(Float)
    mes_04 = Column(Float)
    mes_03 = Column(Float)
    mes_02 = Column(Float)
    mes_01 = Column(Float)
    mes_parcial = Column(Float)
    
    # Semanas Anteriores
    semana_anterior_5 = Column(Float)
    freq_semana_anterior_5 = Column(Float)
    qtde_semana_anterior_5 = Column(Float)
    media_semana_anterior_5 = Column(Float)
    
    semana_anterior_4 = Column(Float)
    freq_semana_anterior_4 = Column(Float)
    qtde_semana_anterior_4 = Column(Float)
    media_semana_anterior_4 = Column(Float)
    
    semana_anterior_3 = Column(Float)
    freq_semana_anterior_3 = Column(Float)
    qtde_semana_anterior_3 = Column(Float)
    media_semana_anterior_3 = Column(Float)
    
    semana_anterior_2 = Column(Float)
    freq_semana_anterior_2 = Column(Float)
    qtde_semana_anterior_2 = Column(Float)
    media_semana_anterior_2 = Column(Float)
    
    semana_atual = Column(Float)
    freq_semana_atual = Column(Float)
    qtde_semana_atual = Column(Float)
    media_semana_atual = Column(Float)
    
    # Outros Indicadores
    venda_30dd = Column(Float)
    media_considerada_lv = Column(Float)
    estoque_cd = Column(Float)
    ultima_entrada_data_cd = Column(DateTime)
    ultima_entrada_qtde_cd = Column(Float)
    ultima_entrada_custo_cd = Column(Float)
    estoque_une = Column(Float)
    ultimo_inventario_une = Column(DateTime)
    ultima_entrada_data_une = Column(DateTime)
    ultima_entrada_qtde_une = Column(Float)
    estoque_lv = Column(Float)
    estoque_gondola_lv = Column(Float)
    estoque_ilha_lv = Column(Float)
    exposicao_minima = Column(Float)
    exposicao_minima_une = Column(Float)
    exposicao_maxima_une = Column(Float)
    leadtime_lv = Column(Float)
    ponto_pedido_lv = Column(Float)
    media_travada = Column(Float)
    endereco_reserva = Column(String(255))
    endereco_linha = Column(String(255))
    solicitacao_pendente = Column(String(255))
    solicitacao_pendente_data = Column(DateTime)
    solicitacao_pendente_qtde = Column(Float)
    solicitacao_pendente_situacao = Column(String(255))
    ultima_venda_data_une = Column(DateTime)
    picklist = Column(String(255))
    picklist_situacao = Column(String(255))
    picklist_conferencia = Column(String(255))
    ultimo_volume = Column(String(255))
    volume_qtde = Column(Float)
    romaneio_solicitacao = Column(String(255))
    romaneio_envio = Column(String(255))
    nota = Column(String(255))
    serie = Column(String(255))
    nota_emissao = Column(DateTime)
    freq_ult_sem = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Admmatao(id={self.id}, produto='{self.nome}')>"
