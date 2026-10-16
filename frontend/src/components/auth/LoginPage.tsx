import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useRole } from '../../context/RoleContext';
import {
  BookOpen,
  ShieldCheck,
  User,
  ArrowRight,
  Loader2,
  Sparkles,
  Layers,
  Inbox,
  AlertCircle,
  Building2,
} from 'lucide-react';

function GoogleIcon() {
  return (
    <svg className="w-5 h-5 shrink-0" viewBox="0 0 24 24">
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
      />
    </svg>
  );
}

export function LoginPage() {
  const { loginAs, loginWithGoogle, isLoading } = useRole();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [pendingAction, setPendingAction] = useState<'google' | 'patron' | 'librarian' | null>(null);

  const handleGoogleLogin = async () => {
    setError(null);
    setPendingAction('google');
    try {
      await loginWithGoogle();
      // Supabase OAuth redirects window.location.href automatically
    } catch (err: any) {
      setError(err?.message || 'Failed to initiate Google sign-in.');
      setPendingAction(null);
    }
  };

  const handleDemoLogin = async (role: 'PATRON' | 'LIBRARIAN') => {
    setError(null);
    setPendingAction(role.toLowerCase() as 'patron' | 'librarian');
    try {
      await loginAs(role);
      navigate('/catalog');
    } catch (err: any) {
      setError(err?.message || `Failed to sign in as ${role}.`);
    } finally {
      setPendingAction(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-slate-100 flex flex-col justify-center items-center px-4 sm:px-6 lg:px-8 py-12 relative overflow-hidden">
      {/* Background Decorative Rings */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-80 h-80 bg-violet-600/10 rounded-full blur-2xl pointer-events-none" />

      <div className="w-full max-w-xl z-10 space-y-8">
        {/* Brand Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white shadow-xl shadow-indigo-500/25 border border-indigo-400/30 mb-1">
            <Building2 className="w-7 h-7" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
            Metropolitan Library
          </h1>
          <p className="text-sm sm:text-base text-slate-400 font-medium max-w-md mx-auto">
            Intelligent Catalog & Circulation Management System with Autonomous AI Agent
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-3.5 bg-rose-500/15 border border-rose-500/30 rounded-xl text-rose-200 text-xs sm:text-sm flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Main Auth Card */}
        <div className="bg-slate-800/80 backdrop-blur-xl border border-slate-700/80 rounded-3xl p-6 sm:p-8 shadow-2xl space-y-6">
          {/* Section 1: Live Google Single Sign-On */}
          <div className="space-y-3">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Patron Single Sign-On (SSO)
            </h2>
            <button
              type="button"
              disabled={isLoading || pendingAction !== null}
              onClick={handleGoogleLogin}
              className="w-full py-3.5 px-4 rounded-xl bg-white hover:bg-slate-100 text-slate-900 font-semibold text-sm shadow-lg shadow-black/20 hover:shadow-black/30 transition-all duration-200 flex items-center justify-center space-x-3 cursor-pointer disabled:opacity-50 active:scale-[0.99]"
            >
              {pendingAction === 'google' ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin text-slate-700" />
                  <span>Redirecting to Google...</span>
                </>
              ) : (
                <>
                  <GoogleIcon />
                  <span>Continue with Google</span>
                  <ArrowRight className="w-4 h-4 text-slate-400 ml-1" />
                </>
              )}
            </button>
            <p className="text-[11px] text-slate-400 px-1 pt-1 text-center">
              Authenticates securely via Google OAuth
            </p>
          </div>

          {/* Section Divider */}
          <div className="relative flex items-center justify-center">
            <div className="border-t border-slate-700/80 w-full" />
            <span className="bg-slate-800 px-3 text-[11px] font-bold text-slate-400 uppercase tracking-widest absolute">
              or explore demo accounts
            </span>
          </div>

          {/* Section 2: Preset Demo Roles */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* 1. Patron Demo Card */}
            <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-700/60 flex flex-col justify-between space-y-4 hover:border-indigo-500/50 transition-colors">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="w-8 h-8 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center">
                    <User className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    Patron
                  </span>
                </div>
                <div>
                  <h3 className="font-bold text-sm text-white">Demo Patron</h3>
                  <p className="text-[11px] text-slate-400 font-mono">patron@example.com</p>
                </div>
                <ul className="text-[11px] text-slate-400 space-y-1 pt-1">
                  <li className="flex items-center space-x-1.5">
                    <span className="w-1 h-1 rounded-full bg-indigo-400" />
                    <span>Catalog Semantic Search</span>
                  </li>
                  <li className="flex items-center space-x-1.5">
                    <span className="w-1 h-1 rounded-full bg-indigo-400" />
                    <span>14-Day Book Checkouts</span>
                  </li>
                  <li className="flex items-center space-x-1.5">
                    <span className="w-1 h-1 rounded-full bg-indigo-400" />
                    <span>AI Librarian Chat Assistant</span>
                  </li>
                </ul>
              </div>

              <button
                type="button"
                disabled={isLoading}
                onClick={() => handleDemoLogin('PATRON')}
                className="w-full py-2 px-3 rounded-lg bg-indigo-600/80 hover:bg-indigo-600 text-white font-medium text-xs shadow-xs transition-colors flex items-center justify-center space-x-1.5 cursor-pointer disabled:opacity-50"
              >
                {pendingAction === 'patron' ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <>
                    <span>Sign In as Patron</span>
                    <ArrowRight className="w-3 h-3" />
                  </>
                )}
              </button>
            </div>

            {/* 2. Librarian Demo Card */}
            <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-700/60 flex flex-col justify-between space-y-4 hover:border-amber-500/50 transition-colors">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center">
                    <ShieldCheck className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
                    Staff
                  </span>
                </div>
                <div>
                  <h3 className="font-bold text-sm text-white">Demo Librarian</h3>
                  <p className="text-[11px] text-slate-400 font-mono">librarian@example.com</p>
                </div>
                <ul className="text-[11px] text-slate-400 space-y-1 pt-1">
                  <li className="flex items-center space-x-1.5">
                    <span className="w-1 h-1 rounded-full bg-amber-400" />
                    <span>Catalog Curation (Add/Edit)</span>
                  </li>
                  <li className="flex items-center space-x-1.5">
                    <span className="w-1 h-1 rounded-full bg-amber-400" />
                    <span>Intake Reverse Logistics Desk</span>
                  </li>
                  <li className="flex items-center space-x-1.5">
                    <span className="w-1 h-1 rounded-full bg-amber-400" />
                    <span>Live Queue Inventory Badge</span>
                  </li>
                </ul>
              </div>

              <button
                type="button"
                disabled={isLoading}
                onClick={() => handleDemoLogin('LIBRARIAN')}
                className="w-full py-2 px-3 rounded-lg bg-amber-600/80 hover:bg-amber-600 text-white font-medium text-xs shadow-xs transition-colors flex items-center justify-center space-x-1.5 cursor-pointer disabled:opacity-50"
              >
                {pendingAction === 'librarian' ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <>
                    <span>Sign In as Staff</span>
                    <ArrowRight className="w-3 h-3" />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Footer info */}
        <p className="text-xs text-center text-slate-500">
          Metropolitan Library Management System · Phase 4 Autonomous Agent Edition
        </p>
      </div>
    </div>
  );
}

