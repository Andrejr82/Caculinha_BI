-- Script simplificado: Apenas inserir perfis dos usuários
-- Execute este SQL no Supabase SQL Editor

-- Inserir perfis dos usuários com os IDs corretos
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
    ON CONFLICT (id) DO UPDATE SET role = 'admin', username = 'admin', full_name = 'Administrator';
    
    RAISE NOTICE 'Admin profile created/updated: %', admin_id;
  ELSE
    RAISE NOTICE 'Admin user not found!';
  END IF;
  
  -- Inserir perfil do user
  IF user_id IS NOT NULL THEN
    INSERT INTO public.user_profiles (id, username, role, full_name)
    VALUES (user_id, 'user', 'user', 'Test User')
    ON CONFLICT (id) DO UPDATE SET role = 'user', username = 'user', full_name = 'Test User';
    
    RAISE NOTICE 'User profile created/updated: %', user_id;
  ELSE
    RAISE NOTICE 'User not found!';
  END IF;
END $$;

-- Verificar resultado
SELECT 
  u.email,
  p.username,
  p.role,
  p.full_name
FROM auth.users u
LEFT JOIN public.user_profiles p ON u.id = p.id
WHERE u.email IN ('admin@agentbi.com', 'user@agentbi.com');
