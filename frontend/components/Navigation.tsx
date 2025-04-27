import { useAuth } from '@/utils/auth';
import Link from 'next/link';
import { useState } from 'react';

export default function Navigation() {
  const { user, signOut } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  const handleSignOut = async () => {
    try {
      setIsLoading(true);
      await signOut();
    } catch (error) {
      console.error('Error signing out:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <nav className="bg-blue-600 text-white shadow-md">
      <div className="container mx-auto px-4 py-3 flex justify-between items-center">
        <Link href="/" passHref>
          <span className="text-xl font-bold cursor-pointer">Sound Event Detection</span>
        </Link>

        {user && (
          <div className="flex items-center space-x-4">
            <span className="text-sm hidden sm:inline">
              {user.email}
            </span>
            <button
              onClick={handleSignOut}
              disabled={isLoading}
              className="bg-white text-blue-600 px-3 py-1 rounded-md hover:bg-blue-50 transition disabled:opacity-50"
            >
              {isLoading ? 'Signing out...' : 'Sign out'}
            </button>
          </div>
        )}
      </div>
    </nav>
  );
} 