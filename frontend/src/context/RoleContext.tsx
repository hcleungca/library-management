import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { UserRole, TokenUser, TokenResponse } from '@/types';
import { apiFetch } from '@/lib/api';
import { getSupabase } from '@/lib/supabase';

export interface RoleContextType {
  role: UserRole;
  isLibrarian: boolean;
  isPatron: boolean;
  currentUser: TokenUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setRole: (role: UserRole) => Promise<void>;
  loginAs: (role: UserRole) => Promise<void>;
  loginSSO: () => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  handleOAuthSession: (session: any) => Promise<void>;
  logout: () => void;
}

const RoleContext = createContext<RoleContextType | undefined>(undefined);

const DEMO_ROLE_STORAGE_KEY = 'app_demo_role';
const AUTH_TOKEN_STORAGE_KEY = 'auth_token';
const AUTH_USER_STORAGE_KEY = 'auth_user';

interface RoleProviderProps {
  children: ReactNode;
}

export function RoleProvider({ children }: RoleProviderProps) {
  const queryClient = useQueryClient();

  // Rehydrate current user from localStorage if exists
  const [currentUser, setCurrentUser] = useState<TokenUser | null>(() => {
    if (typeof window !== 'undefined') {
      const savedToken = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
      const savedUser = localStorage.getItem(AUTH_USER_STORAGE_KEY);
      if (savedToken && savedUser) {
        try {
          return JSON.parse(savedUser) as TokenUser;
        } catch {
          return null;
        }
      }
    }
    return null;
  });

  const [role, setRoleState] = useState<UserRole>(() => {
    if (currentUser?.role) {
      return currentUser.role;
    }
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(DEMO_ROLE_STORAGE_KEY);
      if (saved === 'LIBRARIAN' || saved === 'PATRON') {
        return saved;
      }
    }
    return 'PATRON';
  });

  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Core login handler: fetches fresh signed JWT from backend and persists session
  const loginAs = useCallback(
    async (targetRole: UserRole): Promise<void> => {
      setIsLoading(true);
      try {
        const response = await apiFetch<TokenResponse>('/auth/demo-token', {
          method: 'POST',
          body: JSON.stringify({ role: targetRole }),
        });

        if (typeof window !== 'undefined') {
          localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, response.access_token);
          localStorage.setItem(AUTH_USER_STORAGE_KEY, JSON.stringify(response.user));
          localStorage.setItem(DEMO_ROLE_STORAGE_KEY, targetRole);
        }

        setRoleState(targetRole);
        setCurrentUser(response.user);

        // Wipe stale query cache and refetch for new identity
        await queryClient.invalidateQueries();
      } catch (err) {
        console.error(`Failed to sign in as ${targetRole}:`, err);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [queryClient]
  );

  // Single Sign-On (SSO): Logs in as verified library Patron with dedicated SSO identity
  const loginSSO = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    try {
      const response = await apiFetch<TokenResponse>('/auth/sso-token', {
        method: 'POST',
      });

      if (typeof window !== 'undefined') {
        localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, response.access_token);
        localStorage.setItem(AUTH_USER_STORAGE_KEY, JSON.stringify(response.user));
        localStorage.setItem(DEMO_ROLE_STORAGE_KEY, 'PATRON');
      }

      setRoleState('PATRON');
      setCurrentUser(response.user);

      // Invalidate queries so components rehydrate with the SSO token
      await queryClient.invalidateQueries();
    } catch (err) {
      console.error('Failed to sign in via SSO:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [queryClient]);

  // Live Supabase Google OAuth Redirect
  const loginWithGoogle = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    try {
      const supabase = await getSupabase();
      const redirectUrl = `${window.location.origin}/auth/callback`;
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: redirectUrl,
        },
      });

      if (error) {
        throw error;
      }

      if (data?.url) {
        window.location.href = data.url;
      }
    } catch (err) {
      console.error('Failed to initiate Google OAuth:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Process session callback from Supabase OAuth
  const handleOAuthSession = useCallback(
    async (session: any): Promise<void> => {
      if (!session?.access_token) {
        throw new Error('No access token in OAuth session');
      }

      const token = session.access_token;
      const user = session.user;
      const email = user?.email || '';
      const fullName =
        user?.user_metadata?.full_name ||
        user?.user_metadata?.name ||
        (email ? email.split('@')[0] : 'Patron');

      const tokenUser: TokenUser = {
        id: user.id,
        email: email,
        full_name: fullName,
        role: 'PATRON',
      };

      if (typeof window !== 'undefined') {
        localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
        localStorage.setItem(AUTH_USER_STORAGE_KEY, JSON.stringify(tokenUser));
        localStorage.setItem(DEMO_ROLE_STORAGE_KEY, 'PATRON');
      }

      setRoleState('PATRON');
      setCurrentUser(tokenUser);
      await queryClient.invalidateQueries();
    },
    [queryClient]
  );

  // Logout handler: clears session tokens and flushes query client
  const logout = useCallback(() => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
      localStorage.removeItem(AUTH_USER_STORAGE_KEY);
      localStorage.removeItem(DEMO_ROLE_STORAGE_KEY);
    }
    setCurrentUser(null);
    setRoleState('PATRON');
    queryClient.clear();
  }, [queryClient]);

  // Backward compatibility: alias setRole to loginAs
  const setRole = loginAs;

  const value: RoleContextType = {
    role,
    isLibrarian: role === 'LIBRARIAN',
    isPatron: role === 'PATRON',
    currentUser,
    isAuthenticated: Boolean(currentUser && typeof window !== 'undefined' && localStorage.getItem(AUTH_TOKEN_STORAGE_KEY)),
    isLoading,
    setRole,
    loginAs,
    loginSSO,
    loginWithGoogle,
    handleOAuthSession,
    logout,
  };

  return <RoleContext.Provider value={value}>{children}</RoleContext.Provider>;
}

export function useRole(): RoleContextType {
  const context = useContext(RoleContext);
  if (!context) {
    throw new Error('useRole must be used within a RoleProvider');
  }
  return context;
}
