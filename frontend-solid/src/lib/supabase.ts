/**
 * Supabase Client Configuration for Frontend
 */

import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://nmamxbriulivinlqqbmf.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5tYW14YnJpdWxpdmlubHFxYm1mIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMzMjM2MDEsImV4cCI6MjA3ODg5OTYwMX0.Mf-CTCPqQ6zjA0Aqa2oQoWhyVjG4SbNX9O7mR7rfW5I'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
