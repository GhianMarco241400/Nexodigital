import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  Link,
  createRootRouteWithContext,
  redirect,
  useNavigate,
  useRouter,
  HeadContent,
  Scripts,
  type ErrorComponentProps,
  useLocation,
} from "@tanstack/react-router";
import { useEffect, type ReactNode } from "react";
import { AppShell, DemoProvider } from '@/components/salesia/shell';
import { AuthProvider, useAuth } from '@/modules/auth/AuthProvider';
import { getToken } from '@/modules/auth/token';
import { Button } from '@/components/ui/button';

import appCss from "../styles.css?url";
import { reportLovableError } from "../lib/lovable-error-reporting";

function NotFoundComponent() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-7xl font-bold text-foreground">404</h1>
        <h2 className="mt-4 text-xl font-semibold text-foreground">Page not found</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="mt-6">
          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Go home
          </Link>
        </div>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: ErrorComponentProps) {
  console.error(error);
  const router = useRouter();
  useEffect(() => {
    reportLovableError(error, { boundary: "tanstack_root_error_component" });
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-xl font-semibold tracking-tight text-foreground">
          This page didn't load
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Something went wrong on our end. You can try refreshing or head back home.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <Button
            onClick={() => {
              router.invalidate();
              reset();
            }}
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Try again
          </Button>
          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent"
          >
            Go home
          </Link>
        </div>
      </div>
    </div>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "SalesIA · Gestión comercial" },
      { name: "description", content: "SalesIA, el espacio de gestión comercial para tu equipo." },
      { property: "og:title", content: "SalesIA · Gestión comercial" },
      { property: "og:description", content: "Gestión interna de ventas, pedidos y análisis comercial." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
    links: [
      { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
      { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossOrigin: 'anonymous' },
      { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;650;700;750;800&display=swap' },
      {
        rel: "stylesheet",
        href: appCss,
      },
      { rel: "icon", href: "/favicon.ico", type: "image/x-icon" },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
  beforeLoad: ({ location }) => {
    if (typeof window === "undefined") return;
    const authenticated = getToken() !== null;
    const isLogin = location.pathname === "/login";
    if (!authenticated && !isLogin) {
      throw redirect({ to: "/login" });
    }
  },
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang="es">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RootFrame />
      </AuthProvider>
    </QueryClientProvider>
  );
}

function SessionLoading() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="flex flex-col items-center gap-3 text-muted-foreground">
        <div className="size-8 animate-spin rounded-full border-2 border-muted border-t-primary" />
        <span className="text-sm">Cargando tu espacio de trabajo…</span>
      </div>
    </div>
  );
}

function RootFrame() {
  const { pathname } = useLocation();
  const { isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const isLogin = pathname === "/login";

  useEffect(() => {
    if (!isLoading && !isAuthenticated && !isLogin) {
      navigate({ to: "/login", replace: true });
    }
    if (!isLoading && isAuthenticated && isLogin) {
      navigate({ to: "/", replace: true });
    }
  }, [isLoading, isAuthenticated, isLogin, navigate]);

  if (isLogin) {
    return (
      <DemoProvider>
        <Outlet />
      </DemoProvider>
    );
  }

  if (isLoading) return <SessionLoading />;
  if (!isAuthenticated) return <SessionLoading />;

  return (
    <DemoProvider>
      <AppShell>
        <Outlet />
      </AppShell>
    </DemoProvider>
  );
}
