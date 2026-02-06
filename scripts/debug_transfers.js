/**
 * DIAGNÓSTICO DE CLIQUES - Cole no Console do Navegador
 * 
 * Abre DevTools (F12), vai em Console, e cola este script.
 * Ele vai monitorar EXATAMENTE o que está acontecendo nos cliques.
 */

// 1. Monitor de logs personalizados
window.__transferDebug = {
  clicks: [],
  stateChanges: [],
  
  logClick: (uneId, mode, isCheckbox) => {
    console.log(`🖱️ CLIQUE REGISTRADO: UNE ${uneId} | Modo: ${mode} | Tipo: ${isCheckbox ? 'checkbox' : 'radio'}`);
    window.__transferDebug.clicks.push({
      timestamp: new Date().toISOString(),
      uneId,
      mode,
      isCheckbox
    });
  },
  
  logStateChange: (field, oldValue, newValue) => {
    console.log(`🔄 ESTADO ALTERADO: ${field} | ${oldValue} → ${newValue}`);
    window.__transferDebug.stateChanges.push({
      timestamp: new Date().toISOString(),
      field,
      oldValue,
      newValue
    });
  },
  
  summary: () => {
    console.log(`\n📊 RESUMO DE DIAGNÓSTICO:`);
    console.log(`Total de cliques: ${window.__transferDebug.clicks.length}`);
    console.log(`Total de mudanças de estado: ${window.__transferDebug.stateChanges.length}`);
    console.log(`Cliques:`, window.__transferDebug.clicks);
    console.log(`Mudanças:`, window.__transferDebug.stateChanges);
  }
};

// 2. Detector de eventos de clique
document.addEventListener('click', (e) => {
  const target = e.target as HTMLElement;
  const input = target.closest('input[type="checkbox"], input[type="radio"]');
  if (input) {
    const parent = input.closest('div[onclick]');
    console.log('✅ INPUT CLICADO:', {
      type: input.getAttribute('type'),
      checked: (input as HTMLInputElement).checked,
      parent: parent?.className.substring(0, 50)
    });
  }
}, true);

// 3. Atalho rápido
console.log(`
📋 COMANDOS DISPONÍVEIS:
- window.__transferDebug.summary() → ver resumo
- window.__transferDebug.clicks → ver todos os cliques
- window.__transferDebug.stateChanges → ver mudanças de estado
`);

console.log('✅ Diagnóstico ativado! Agora clique nas UNEs e veja o log.');
