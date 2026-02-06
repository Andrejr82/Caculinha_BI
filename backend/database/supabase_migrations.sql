-- Enable UUID extension if not enabled
create extension if not exists "uuid-ossp";

-- Create a table for public user profiles
create table if not exists public.user_profiles (
  id uuid references auth.users on delete cascade not null primary key,
  username text unique,
  role text default 'user' check (role in ('user', 'admin', 'manager')),
  full_name text,
  avatar_url text,
  allowed_segments jsonb default '[]'::jsonb,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable Row Level Security (RLS)
alter table public.user_profiles enable row level security;

-- Create policies
create policy "Public profiles are viewable by everyone."
  on public.user_profiles for select
  using ( true );

create policy "Users can insert their own profile."
  on public.user_profiles for insert
  with check ( auth.uid() = id );

create policy "Users can update their own profile."
  on public.user_profiles for update
  using ( auth.uid() = id );

-- Create a function to handle new user signup
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.user_profiles (id, username, role, full_name, allowed_segments)
  values (
    new.id,
    split_part(new.email, '@', 1), -- Default username from email
    'user', -- Default role
    new.raw_user_meta_data->>'full_name',
    coalesce(new.raw_user_meta_data->'allowed_segments', '[]'::jsonb)
  );
  return new;
end;
$$;

-- Create the trigger
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Optional: Backfill existing users (Run this manually if needed)
-- insert into public.user_profiles (id, username, role)
-- select id, split_part(email, '@', 1), 'user'
-- from auth.users
-- where id not in (select id from public.user_profiles);
