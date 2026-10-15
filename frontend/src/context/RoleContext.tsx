import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useRef,
  useCallback,
  ReactNode,
} from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { UserRole, TokenUser, TokenResponse } from '@/types';
import { apiFetch } from '@/lib/api';

export interface RoleContextType {
  role: UserRole;
  setRole: (role: UserRole) => Promise<void>;
  isLibrarian: boolean;
  isPatron: boolean;
  currentUser: TokenUser | null;
  isLoading: boolean;
}

const RoleContext = createContext<RoleContextType | undefined>(undefined);

const DEMO_ROLE_STORAGE_KEY = 'app_demo_role';
const AUTH_TOKEN_STORAGE_KEY = 'auth_token';

interface RoleProviderProps {
  children: ReactNode;
}

export function RoleProvider({ children }: RoleProviderProps) {
  const queryClient = useQueryClient();

  // Read initial role from localStorage if valid, otherwise default to PATRON
  const [role, setRoleState] = useState<UserRole>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(DEMO_ROLE_STORAGE_KEY);
      if (saved === 'LIBRARIAN' || saved === 'PATRON') {
        return saved;
      }
    }
    return 'PATRON';
  });

  const [currentUser, setCurrentUser] = useState<TokenUser | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Concurrency Defense: Tracks the most recent requested role to discard stale async responses
  const latestRequestRef = useRef<UserRole>(role);

  const fetchTokenForRole = useCallback(
    async (targetRole: UserRole): Promise<void> => {
      latestRequestRef.current = targetRole;
      setIsLoading(true);

      try {
        const response = await apiFetch<TokenResponse>('/auth/demo-token', {
          method: 'POST',
          body: JSON.stringify({ role: targetRole }),
        });

        // Race condition guard: If user toggled to another role while this request was inflight, ignore
        if (latestRequestRef.current !== targetRole) {
          return;
        }

        if (typeof window !== 'undefined') {
          localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, response.access_token);
          localStorage.setItem(DEMO_ROLE_STORAGE_KEY, targetRole);
        }

        setRoleState(targetRole);
        setCurrentUser(response.user);

        // Invalidate queries so all active components refetch with the new token
        await queryClient.invalidateQueries();
      } catch (err) {
        console.error(`Failed to acquire demo token for ${targetRole}:`, err);
      } finally {
        if (latestRequestRef.current === targetRole) {
          setIsLoading(false);
        }
      }
    },
    [queryClient]
  );

  // Mount effect: Fetch initial token if not already in localStorage or if user info is null
  useEffect(() => {
    const existingToken = typeof window !== 'undefined' ? localStorage.getItem(AUTH_TOKEN_STORAGE_KEY) : null;
    if (!existingToken || !currentUser) {
      fetchTokenForRole(role);
    }
  }, [fetchTokenForRole, role, currentUser]);

  const setRole = useCallback(
    async (newRole: UserRole): Promise<void> => {
      if (newRole === role && currentUser) {
        return;
      }
      await fetchTokenForRole(newRole);
    },
    [role, currentUser, fetchTokenForRole]
  );

  const value: RoleContextType = {
    role,
    setRole,
    isLibrarian: role === 'LIBRARIAN',
    isPatron: role === 'PATRON',
    currentUser,
    isLoading,
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

