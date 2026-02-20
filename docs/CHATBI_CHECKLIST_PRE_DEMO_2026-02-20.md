# ChatBI - Checklist Técnico Pré-Demo (20/02/2026)

## Como usar
- Execute os itens na ordem.
- Marque `OK` ou `FALHOU`.
- Se falhar, use a ação de contingência da mesma linha.

## Janela sugerida
- Início: 30 minutos antes da demo.
- Duração total: 10 a 15 minutos.

## Checklist rápido
| # | Verificação | Resultado esperado | Status | Contingência imediata |
|---|---|---|---|---|
| 1 | Backend iniciado | Sem traceback crítico no startup |  | Reiniciar backend e validar `.env` |
| 2 | Frontend iniciado | Página abre sem erro JS |  | Reiniciar frontend e limpar cache (Ctrl+F5) |
| 3 | Login funcional | Usuário entra e acessa ChatBI |  | Refazer login e validar token |
| 4 | Stream token | `POST /api/v1/chat/stream-token` retorna `200` |  | Validar autenticação e horário do sistema |
| 5 | Chat stream | Pergunta simples responde em streaming |  | Nova sessão e pergunta curta |
| 6 | Resposta tabular | Pergunta de listagem retorna tabela |  | Trocar para consulta mais objetiva |
| 7 | Resposta com gráfico | Pergunta analítica retorna gráfico |  | Usar pergunta curinga já validada |
| 8 | Exportação conversa | Export JSON/MD/TXT funciona |  | Exportar só JSON como fallback |
| 9 | Feedback | `👍/👎` sem erro 500 |  | Recarregar página e tentar novamente |
| 10 | Perfil/escopo | Usuário vê escopo correto (role/RLS) |  | Trocar para usuário de demo validado |

## Perguntas curinga para demo
1. `Como estão as vendas por UNE nos últimos 30 dias?`
2. `Mostre itens com maior risco de ruptura por segmento.`
3. `Quais categorias têm maior margem e menor giro?`

## Critério de “pronto para apresentar”
- Itens 1 a 7: obrigatórios em `OK`.
- Itens 8 a 10: ao menos 2 em `OK`.

## Plano B (se houver instabilidade)
- Usar sessão já aquecida no navegador.
- Priorizar perguntas curinga.
- Evitar consultas muito longas na abertura.
- Mostrar matriz de go-live e próximos passos enquanto estabiliza.
