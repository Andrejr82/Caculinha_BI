-- Script SQL para criar usuários de teste no Supabase
-- Execute este script no SQL Editor do Supabase Dashboard

-- 1. Criar usuário ADMIN
-- Email: admin@agentbi.com
-- Senha: Admin@2024
INSERT INTO auth.users (
  instance_id,
  id,
  aud,
  role,
  email,
  encrypted_password,
  email_confirmed_at,
  recovery_sent_at,
  last_sign_in_at,
  raw_app_meta_data,
  raw_user_meta_data,
  created_at,
  updated_at,
  confirmation_token,
  email_change,
  email_change_token_new,
  recovery_token
) VALUES (
  '00000000-0000-0000-0000-000000000000',
  gen_random_uuid(),
  'authenticated',
  'authenticated',
  'admin@agentbi.com',
  crypt('Admin@2024', gen_salt('bf')),
  NOW(),
  NOW(),
  NOW(),
  '{"provider":"email","providers":["email"]}',
  '{}',
  NOW(),
  NOW(),
  '',
  '',
  '',
  ''
);

-- 2. Criar usuário COMUM
-- Email: user@agentbi.com
-- Senha: User@2024
INSERT INTO auth.users (
  instance_id,
  id,
  aud,
  role,
  email,
  encrypted_password,
  email_confirmed_at,
  recovery_sent_at,
  last_sign_in_at,
  raw_app_meta_data,
  raw_user_meta_data,
  created_at,
  updated_at,
  confirmation_token,
  email_change,
  email_change_token_new,
  recovery_token
) VALUES (
  '00000000-0000-0000-0000-000000000000',
  gen_random_uuid(),
  'authenticated',
  'authenticated',
  'user@agentbi.com',
  crypt('User@2024', gen_salt('bf')),
  NOW(),
  NOW(),
  NOW(),
  '{"provider":"email","providers":["email"]}',
  '{}',
  NOW(),
  NOW(),
  '',
  '',
  '',
  ''
);

-- 3. (OPCIONAL) Criar tabela de perfis para armazenar role
CREATE TABLE IF NOT EXISTS public.user_profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  username TEXT UNIQUE,
  role TEXT DEFAULT 'user',
  full_name TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. (OPCIONAL) Habilitar RLS na tabela de perfis
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- 5. (OPCIONAL) Política RLS: usuários podem ver apenas seu próprio perfil
CREATE POLICY "Users can view own profile"
ON public.user_profiles FOR SELECT
USING (auth.uid() = id);

-- 6. (OPCIONAL) Política RLS: usuários podem atualizar apenas seu próprio perfil
CREATE POLICY "Users can update own profile"
ON public.user_profiles FOR UPDATE
USING (auth.uid() = id);

-- 7. (OPCIONAL) Inserir perfis para os usuários criados
-- Você precisará substituir os UUIDs pelos IDs reais dos usuários criados acima
-- Para obter os IDs, execute: SELECT id, email FROM auth.users;

-- Exemplo (substitua os UUIDs):
-- INSERT INTO public.user_profiles (id, username, role, full_name)
-- VALUES 
--   ('uuid-do-admin-aqui', 'admin', 'admin', 'Administrator'),
--   ('uuid-do-user-aqui', 'user', 'user', 'Test User');

-- IMPORTANTE: Após executar este script, execute:
-- SELECT id, email FROM auth.users WHERE email IN ('admin@agentbi.com', 'user@agentbi.com');
-- E anote os UUIDs para usar no passo 7 (se quiser criar a tabela user_profiles)
