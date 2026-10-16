import { createClient, SupabaseClient } from '@supabase/supabase-js';

let supabaseClient: SupabaseClient | null = null;

export async function getSupabase(): Promise<SupabaseClient> {
  if (supabaseClient) {
    return supabaseClient;
  }

  // 1. Check Vite env variables if provided
  let supabaseUrl = (import.meta as any).env?.VITE_SUPABASE_URL;
  let supabaseAnonKey = (import.meta as any).env?.VITE_SUPABASE_ANON_KEY;

  // 2. Fetch public configuration from backend /api/auth/config
  if (!supabaseUrl || !supabaseAnonKey) {
    try {
      const res = await fetch('/api/auth/config');
      if (res.ok) {
        const config = await res.json();
        supabaseUrl = config.supabase_url;
        supabaseAnonKey = config.supabase_anon_key;
      }
    } catch (e) {
      console.warn('Could not retrieve Supabase config from API:', e);
    }
  }

  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error(
      'Supabase configuration missing. Ensure SUPABASE_URL and SUPABASE_KEY are configured.'
    );
  }

  supabaseClient = createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,
      flowType: 'pkce',
    },
  });

  return supabaseClient;
}

