import ProtectedRoute from '@/components/Auth/ProtectedRoute';
import Navigation from '@/components/Navigation';
import '@/styles/globals.css';
import { AuthProvider } from '@/utils/auth';
import type { AppProps } from 'next/app';

// Pages that don't require authentication
const publicPages: string[] = [];

function MyApp({ Component, pageProps, router }: AppProps) {
  const isPublicPage = publicPages.includes(router.pathname);

  return (
    <AuthProvider>
      {isPublicPage ? (
        <>
          <Navigation />
          <Component {...pageProps} />
        </>
      ) : (
        <ProtectedRoute>
          <Navigation />
          <Component {...pageProps} />
        </ProtectedRoute>
      )}
    </AuthProvider>
  );
}

export default MyApp; 