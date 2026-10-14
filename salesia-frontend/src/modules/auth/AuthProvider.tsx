import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { UNAUTHORIZED_EVENT, apiPost, request } from "@/services/api";
import { clearToken, getToken, hasToken, setToken } from "@/modules/auth/token";
import type { ApiUser, LoginResponse } from "@/types/api";

export interface AuthContextValue {
  user: ApiUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<ApiUser | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(() => hasToken());

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setIsLoading(false);
      return;
    }

    let active = true;
    request<ApiUser>("/auth/me")
      .then((me) => {
        if (active) setUser(me);
      })
      .catch(() => {
        if (!active) return;
        clearToken();
        setUser(null);
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const onUnauthorized = () => {
      clearToken();
      setUser(null);
      queryClient.clear();
      toast.error("Tu sesión venció. Inicia sesión de nuevo.");
    };
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
  }, [queryClient]);

  const login = useCallback(async (email: string, password: string) => {
    const result = await apiPost<LoginResponse>("/auth/login", { email, password });
    setToken(result.access_token);
    setUser(result.user);
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    queryClient.clear();
  }, [queryClient]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: user !== null,
      isLoading,
      login,
      logout,
    }),
    [user, isLoading, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth debe usarse dentro de AuthProvider");
  }
  return context;
}
