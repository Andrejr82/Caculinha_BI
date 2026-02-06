# Correção de Login Supabase (Admin)

O problema de login com o usuário `admin` foi diagnosticado e corrigido.

## Diagnóstico
1. O usuário `admin` existia no **Supabase Auth** (como `admin@agentbi.com`), mas não tinha um perfil correspondente na tabela `user_profiles`.
2. O sistema tenta buscar o email associado ao username `admin` na tabela `user_profiles`. Como o perfil não existia, a busca falhava ou não atribuía as permissões corretas.
3. Ao tentar corrigir, descobrimos que a tabela `user_profiles` no Supabase não possui a coluna `allowed_segments`, causando erro no script de correção.

## Solução Aplicada
1. **Script de Correção Ajustado**: Modificamos o script `backend/fix_supabase_admin.py` para:
    - Utilizar a chave de serviço (Service Role Key) para bypassar restrições de segurança (RLS) ao criar o perfil.
    - Ignorar a coluna `allowed_segments` (que não existe no banco), confiando na lógica do backend que atribui acesso total (`['*']`) automaticamente para administradores.
2. **Execução da Correção**: Rodamos o script ajustado, que criou com sucesso o perfil do admin com role `admin`.
3. **Validação**: Executamos um teste simulado (`backend/test_supabase_login.py`) confirmando que o login com `username="admin"` e `password="admin123"` agora funciona corretamente e retorna as permissões esperadas.

## Próximos Passos para Você
Para que a correção surta efeito na aplicação em execução:

1. **Reinicie o Backend**: Se o servidor estiver rodando, pare-o e inicie novamente.
2. **Login**: Tente fazer login novamente com:
   - **Usuário**: `admin`
   - **Senha**: `admin123`

> **Nota**: Se ainda tiver problemas, tente limpar o cache do navegador ou usar uma janela anônima para garantir que tokens antigos não interfiram.
