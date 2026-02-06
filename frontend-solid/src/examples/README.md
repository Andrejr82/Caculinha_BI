# Exemplos e Demonstrações

Esta pasta contém páginas de exemplo e demonstração criadas durante a migração para SolidJS.

## 📁 Arquivos

### ComponentsDemo.tsx
Demonstração dos primeiros componentes migrados:
- Button (6 variantes × 6 tamanhos)
- Badge (4 variantes)
- Skeleton (loading states)
- Exemplos de integração

### SkeletonDemo.tsx
Demonstração específica do componente Skeleton:
- Basic skeleton
- Card skeleton
- List skeleton
- Table skeleton

### MinimalLogin.tsx
Versão minimalista da página de login para testes.

## 🎯 Propósito

Estes arquivos foram criados durante a migração React → SolidJS para:
- Validar visualmente os componentes migrados
- Servir como referência de uso
- Testar funcionalidades
- Demonstrar integração entre componentes

## ⚠️ Nota

Estes arquivos **NÃO são necessários** para a aplicação em produção.
São apenas para desenvolvimento, testes e referência.

## 🚀 Como Usar

Para acessar estas páginas em desenvolvimento, você precisaria adicionar rotas no `index.tsx`:

```tsx
import ComponentsDemo from './examples/ComponentsDemo';
import SkeletonDemo from './examples/SkeletonDemo';
import MinimalLogin from './examples/MinimalLogin';

// Adicionar rotas:
<Route path="/examples/components" component={ComponentsDemo} />
<Route path="/examples/skeleton" component={SkeletonDemo} />
<Route path="/examples/minimal-login" component={MinimalLogin} />
```

---

**Status:** Arquivos movidos de `src/pages/` para `src/examples/`  
**Data:** 2025-11-30
