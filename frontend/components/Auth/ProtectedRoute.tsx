import { useAuth } from '@/utils/auth';
import { useRouter } from 'next/router';
import AuthPage from './AuthPage';

type ProtectedRouteProps = {
  children: React.ReactNode;
};

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, loading } = useAuth();
  const router = useRouter();

  // If auth is still loading, show a loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  // If no user is found, show the auth page
  if (!user) {
    return <AuthPage />;
  }

  // If user is authenticated, render the children
  return <>{children}</>;
} 