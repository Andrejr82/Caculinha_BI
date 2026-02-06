/**
 * Teste de seleção de Produtos para Transferências (Multi-Seleção)
 */

export const productSelectionChecklist = `
✅ PRÉ-TESTE MANUAL - SELEÇÃO DE PRODUTOS (Abra transfers no navegador):

1. LISTAGEM DE PRODUTOS:
   □ Verifique se cada linha de produto possui um Checkbox à esquerda.
   □ Clique na linha (texto) de um produto → Checkbox deve marcar.
   □ Clique no Checkbox diretamente → Checkbox deve marcar.

2. MULTI-SELEÇÃO:
   □ Selecione o Produto A.
   □ Selecione o Produto B.
   □ Ambos devem estar marcados visualmente (bg-primary/10 e checkbox).
   □ O painel lateral deve mostrar "2 Produtos Selecionados".

3. DESSELEÇÃO:
   □ Clique novamente no Produto A.
   □ Produto A deve desmarcar.
   □ Painel lateral deve voltar a mostrar "Detalhe do Produto Selecionado" (apenas B restante).

4. ADICIONAR AO CARRINHO (BULK):
   □ Selecione 3 produtos.
   □ Preencha a Quantidade (ex: 10).
   □ Clique em "Adicionar (3) ao Carrinho".
   □ Verifique se o carrinho recebeu 3 novos itens (um para cada produto).
   □ Verifique se a seleção de produtos foi limpa após adicionar.

5. VALIDAÇÃO:
   □ Tente adicionar sem quantidade → Botão deve estar desabilitado.
   □ Tente adicionar sem UNEs selecionadas → Botão deve estar desabilitado.

Se todos os checkboxes forem ✓, a funcionalidade de múltiplos produtos está correta!
`;

console.log(productSelectionChecklist);
