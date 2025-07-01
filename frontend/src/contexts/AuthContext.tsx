import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiService } from '../services/api';

interface User {
  id: number;
  email: string;
  username: string;
  first_name?: string;
  last_name?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  last_login?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (userData: RegisterData) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

interface RegisterData {
  email: string;
  username: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user && !!token;

  // Initialize auth state from localStorage
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const storedToken = localStorage.getItem('fliplens_token');
        const storedUser = localStorage.getItem('fliplens_user');

        if (storedToken && storedUser) {
          setToken(storedToken);
          
          try {
            const userData = JSON.parse(storedUser);
            setUser(userData);
            
            // Verify token is still valid
            await refreshUser();
          } catch (error) {
            console.error('Error parsing stored user data:', error);
            logout();
          }
        }
      } catch (error) {
        console.error('Error initializing auth:', error);
        logout();
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      setIsLoading(true);
      
      const response = await apiService.login(email, password);
      
      if (response.status === 'success') {
        const { user: userData, token: userToken } = response;
        
        setUser(userData);
        setToken(userToken);
        
        // Store in localStorage
        localStorage.setItem('fliplens_token', userToken);
        localStorage.setItem('fliplens_user', JSON.stringify(userData));
        
        return { success: true };
      } else {
        return { success: false, error: response.message || 'Login failed' };
      }
    } catch (error: any) {
      console.error('Login error:', error);
      return { 
        success: false, 
        error: error.message || 'An unexpected error occurred during login' 
      };
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: RegisterData): Promise<{ success: boolean; error?: string }> => {
    try {
      setIsLoading(true);
      
      const response = await apiService.register(userData);
      
      if (response.status === 'success') {
        const { user: newUser, token: userToken } = response;
        
        setUser(newUser);
        setToken(userToken);
        
        // Store in localStorage
        localStorage.setItem('fliplens_token', userToken);
        localStorage.setItem('fliplens_user', JSON.stringify(newUser));
        
        return { success: true };
      } else {
        return { success: false, error: response.message || 'Registration failed' };
      }
    } catch (error: any) {
      console.error('Registration error:', error);
      return { 
        success: false, 
        error: error.message || 'An unexpected error occurred during registration' 
      };
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    
    // Clear localStorage
    localStorage.removeItem('fliplens_token');
    localStorage.removeItem('fliplens_user');
    
    // Call logout endpoint (optional, for logging purposes)
    if (token) {
      apiService.logout().catch(error => {
        console.error('Logout API call failed:', error);
      });
    }
  };

  const refreshUser = async (): Promise<void> => {
    try {
      if (!token) {
        throw new Error('No token available');
      }
      
      const response = await apiService.getCurrentUser();
      
      if (response.status === 'success') {
        setUser(response.user);
        localStorage.setItem('fliplens_user', JSON.stringify(response.user));
      } else {
        throw new Error('Failed to refresh user data');
      }
    } catch (error) {
      console.error('Error refreshing user:', error);
      logout();
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
