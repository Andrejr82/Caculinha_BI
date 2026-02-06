-- Passo 2: Criar tabela user_profiles e inserir roles
-- Execute este SQL no Supabase SQL Editor

-- 1. Criar tabela de perfis
CREATE TABLE IF NOT EXISTS public.user_profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  role TEXT DEFAULT 'user' NOT NULL,
  full_name TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Habilitar RLS
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- 3. Política RLS: usuários podem ver apenas seu próprio perfil
CREATE POLICY "Users can view own profile"
ON public.user_profiles FOR SELECT
USING (auth.uid() = id);

-- 4. Política RLS: usuários podem atualizar apenas seu próprio perfil
CREATE POLICY "Users can update own profile"
ON public.user_profiles FOR UPDATE
USING (auth.uid() = id);

-- 5. Inserir perfis dos usuários (com os IDs corretos)
-- Primeiro, vamos buscar os IDs dos usuários criados
DO $$
DECLARE
  admin_id UUID;
  user_id UUID;
BEGIN
  -- Buscar ID do admin
  SELECT id INTO admin_id FROM auth.users WHERE email = 'admin@agentbi.com' LIMIT 1;
  
  -- Buscar ID do user
  SELECT id INTO user_id FROM auth.users WHERE email = 'user@agentbi.com' LIMIT 1;
  
  -- Inserir perfil do admin
  IF admin_id IS NOT NULL THEN
    INSERT INTO public.user_profiles (id, username, role, full_name)
    VALUES (admin_id, 'admin', 'admin', 'Administrator')
    ON CONFLICT (id) DO UPDATE SET role = 'admin', username = 'admin';
  END IF;
  
  -- Inserir perfil do user
  IF user_id IS NOT NULL THEN
    INSERT INTO public.user_profiles (id, username, role, full_name)
    VALUES (user_id, 'user', 'user', 'Test User')
    ON CONFLICT (id) DO UPDATE SET role = 'user', username = 'user';
  END IF;
END $$;

-- 6. Verificar se os perfis foram criados
SELECT 
  u.email,
  p.username,
  p.role,
  p.full_name
FROM auth.users u
LEFT JOIN public.user_profiles p ON u.id = p.id
WHERE u.email IN ('admin@agentbi.com', 'user@agentbi.com');
