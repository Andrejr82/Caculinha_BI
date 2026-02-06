# 🔧 GUIA RÁPIDO DE RECUPERAÇÃO

## ⚠️ PROBLEMA ATUAL

Sistema está crashando ao abrir com erro:
```
Dashboard de Negócios
Erro ao carregar métricas
```

## ✅ CAUSA & SOLUÇÃO

| Problema | Causa | Solução |
|----------|-------|---------|
| Não pede login | localStorage com token inválido | Limpar localStorage |
| Dashboard crashado | Token inválido ao carregar KPIs | Fazer login novamente |
| Inputs não funcionam | Sintaxe React em Solid.js | ✅ JÁ FOI CORRIGIDO |

---

## 🚀 3 PASSOS PARA RESOLVER

### PASSO 1: Abrir Developer Tools
```
F12  (ou Ctrl+Shift+I no Linux)
```

### PASSO 2: Limpar localStorage
Vá para a aba **Console** e cole:

```javascript
localStorage.clear(); sessionStorage.clear(); location.reload();
```

### PASSO 3: Pressione Enter
Página recarrega e pede login!

---

## 🎯 APÓS RESOLVER

✅ Sistema pede usuário e senha
✅ Dashboard carrega sem erro
✅ Transferências com inputs funcionando:
   - Mode: 1→1, 1→N, N→N
   - Origin: Seleciona UNE
   - Destination: Seleciona UNE(s)

---

## 📋 CHECKLIST

- [ ] Abrir F12
- [ ] Ir para Console
- [ ] Colar comando de limpeza
- [ ] Pressionar Enter
- [ ] Ver tela de login
- [ ] Login com admin/admin
- [ ] Verificar Dashboard funciona
- [ ] Ir para Transferências
- [ ] Testar 1→1 mode
- [ ] Testar 1→N mode
- [ ] Testar N→N mode

---

## ❓ DÚVIDAS?

Ver arquivos:
- `RESUMO_CORRECOES_FINAL.txt` - Detalhado
- `SOLUCAO_ERRO_LOGIN.txt` - Passo a passo
- `MUDANCAS_IMPLEMENTADAS.md` - Contexto técnico

