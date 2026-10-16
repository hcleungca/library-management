import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getSupabase } from '@/lib/supabase';
import { useRole } from '@/context/RoleContext';
import { Loader2, AlertCircle } from 'lucide-react';

export function AuthCallback() {
  const navigate = useNavigate();
  const { handleOAuthSession } = useRole();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function processAuth() {
      try {
        const supabase = await getSupabase();

        // 1. Check if session already resolved from URL hash/code
        const { data, error: sessionError } = await supabase.auth.getSession();
        if (sessionError) {
          throw sessionError;
        }

        if (data?.session) {
          await handleOAuthSession(data.session);
          if (mounted) {
            navigate('/catalog', { replace: true });
          }
          return;
        }

        // 2. Listen for auth state change if exchange is in progress
        const { data: authListener } = supabase.auth.onAuthStateChange(
          async (event, session) => {
            if (session && mounted) {
              await handleOAuthSession(session);
              navigate('/catalog', { replace: true });
            }
          }
        );

        // Fallback timeout in case no session received within 6s
        const timer = setTimeout(() => {
          if (mounted && !data?.session) {
            setError('Authentication timed out. No valid session was received from Google.');
          }
        }, 6000);

        return () => {
          clearTimeout(timer);
          authListener.subscription.unsubscribe();
        };
      } catch (err: any) {
        if (mounted) {
          setError(err?.message || 'Failed to complete Google authentication.');
        }
      }
    }

    processAuth();

    return () => {
      mounted = false;
    };
  }, [navigate, handleOAuthSession]);

  if (error) {
    return (
      <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col justify-center items-center px-4">
        <div className="bg-slate-800 p-6 rounded-2xl border border-rose-500/30 max-w-md w-full text-center space-y-4 shadow-2xl">
          <AlertCircle className="w-10 h-10 text-rose-400 mx-auto" />
          <h2 className="text-lg font-bold text-white">Authentication Failed</h2>
          <p className="text-sm text-slate-400">{error}</p>
          <button
            onClick={() => navigate('/login')}
            className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-xl cursor-pointer transition-colors"
          >
            Back to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col justify-center items-center space-y-4">
      <Loader2 className="w-10 h-10 animate-spin text-indigo-400" />
      <p className="text-sm text-slate-300 font-medium">Signing you in with Google...</p>
    </div>
  );
}

