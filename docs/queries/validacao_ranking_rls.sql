-- =====================================================
-- Query SQL Server: Validação de Ranking Top 20
-- Compara dados do SQL Server com resultado do Parquet
-- =====================================================

-- IMPORTANTE: Substitua os nomes das tabelas/colunas conforme seu schema

-- 1. Query para Top 20 Produtos Mais Vendidos (GERAL - SEM FILTRO DE SEGMENTO)
-- Use esta query para validar se o admin está vendo dados corretos
SELECT TOP 20
    PRODUTO,
    NOME,
    SUM(VENDA_30DD) AS TOTAL_VENDAS
FROM 
    dbo.ADMMAT  -- Ajuste o nome da tabela conforme seu banco
WHERE
    VENDA_30DD IS NOT NULL
    AND VENDA_30DD > 0
GROUP BY 
    PRODUTO, 
    NOME
ORDER BY 
    TOTAL_VENDAS DESC;

-- =====================================================
-- 2. Query para Top 20 Produtos Mais Vendidos (COM FILTRO DE SEGMENTO)
-- Use esta query para validar se usuário com segmento restrito vê apenas seus dados
-- =====================================================

DECLARE @SegmentoUsuario NVARCHAR(100) = 'ARMARINHO';  -- ⚠️ AJUSTE AQUI O SEGMENTO DO USUÁRIO

SELECT TOP 20
    PRODUTO,
    NOME,
    NOMESEGMENTO,
    SUM(VENDA_30DD) AS TOTAL_VENDAS
FROM 
    dbo.ADMMAT
WHERE
    VENDA_30DD IS NOT NULL
    AND VENDA_30DD > 0
    AND NOMESEGMENTO = @SegmentoUsuario  -- 🔒 FILTRO DE SEGMENTO (RLS)
GROUP BY 
    PRODUTO, 
    NOME,
    NOMESEGMENTO
ORDER BY 
    TOTAL_VENDAS DESC;

-- =====================================================
-- 3. Query para Verificar Distribuição por Segmento
-- Útil para entender quantos produtos cada segmento tem
-- =====================================================

SELECT 
    NOMESEGMENTO,
    COUNT(DISTINCT PRODUTO) AS TOTAL_PRODUTOS,
    SUM(VENDA_30DD) AS TOTAL_VENDAS_SEGMENTO,
    AVG(VENDA_30DD) AS MEDIA_VENDAS
FROM 
    dbo.ADMMAT
WHERE
    VENDA_30DD IS NOT NULL
    AND VENDA_30DD > 0
GROUP BY 
    NOMESEGMENTO
ORDER BY 
    TOTAL_VENDAS_SEGMENTO DESC;

-- =====================================================
-- 4. Query para Validar Dados Específicos da Imagem
-- Baseado nos produtos visíveis na screenshot
-- =====================================================

SELECT 
    PRODUTO,
    NOME,
    NOMESEGMENTO,
    VENDA_30DD AS VENDAS
FROM 
    dbo.ADMMAT
WHERE
    NOME LIKE '%PAPEL CHAMEX%'  -- Produto visível na imagem
    OR NOME LIKE '%TNT 40GRS%'   -- Outro produto da imagem
    OR PRODUTO IN (
        -- Adicione códigos de produtos específicos se souber
        '1200GM', '100/NO', '75GRS'
    )
ORDER BY 
    VENDA_30DD DESC;

-- =====================================================
-- 5. Query de Auditoria: Verificar se RLS está sendo aplicado
-- Compare o resultado COM e SEM filtro
-- =====================================================

-- SEM FILTRO (Admin)
SELECT 'SEM_FILTRO' AS TIPO, COUNT(*) AS TOTAL_REGISTROS, SUM(VENDA_30DD) AS TOTAL_VENDAS
FROM dbo.ADMMAT
WHERE VENDA_30DD > 0

UNION ALL

-- COM FILTRO (Usuário ARMARINHO)
SELECT 'COM_FILTRO_ARMARINHO' AS TIPO, COUNT(*) AS TOTAL_REGISTROS, SUM(VENDA_30DD) AS TOTAL_VENDAS
FROM dbo.ADMMAT
WHERE VENDA_30DD > 0 AND NOMESEGMENTO = 'ARMARINHO';

-- =====================================================
-- INSTRUÇÕES DE USO:
-- =====================================================
-- 1. Execute a Query #1 para validar ranking geral (admin)
-- 2. Execute a Query #2 ajustando @SegmentoUsuario para validar RLS
-- 3. Compare os resultados com o gráfico gerado pelo sistema
-- 4. Se houver divergência, execute Query #5 para auditoria
-- =====================================================
