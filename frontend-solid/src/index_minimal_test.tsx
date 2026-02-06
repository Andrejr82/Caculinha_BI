/* src/index.tsx - TESTE MÍNIMO */
console.log('🚀 TESTE: Script carregado!');

const root = document.getElementById('root');
if (root) {
  root.innerHTML = '<div style="color: white; padding: 20px; font-size: 24px;">✅ TESTE: JavaScript está funcionando!</div>';
  console.log('✅ TESTE: innerHTML definido!');
} else {
  console.error('❌ TESTE: Elemento root não encontrado!');
}
