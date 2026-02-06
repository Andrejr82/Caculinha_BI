export default function MinimalLogin() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', backgroundColor: '#020817', color: '#f8fafc' }}>
      <div style={{ padding: '2rem', backgroundColor: '#0f172a', borderRadius: '0.5rem', border: '1px solid #1e293b', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#38bdf8', textAlign: 'center', marginBottom: '1rem' }}>Login Mínimo</h1>
        <p style={{ color: '#94a3b8', textAlign: 'center' }}>A página está renderizando estaticamente.</p>
        <div style={{ marginTop: '1rem', padding: '0.5rem', backgroundColor: '#1e293b', borderRadius: '0.25rem', color: '#cbd5e1' }}>
            Usuário: Teste<br />Senha: Teste
        </div>
      </div>
    </div>
  );
}
