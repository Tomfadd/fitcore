import { useState, useEffect, createContext, useContext } from 'react';
import { getMe } from '../api/endpoints';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = sessionStorage.getItem('access_token');
    if (token) {
      getMe().then(r => setUser(r.data)).catch(() => sessionStorage.removeItem('access_token')).finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const signIn = (token, userData) => {
    sessionStorage.setItem('access_token', token);
    setUser(userData);
  };

  const signOut = () => {
    sessionStorage.removeItem('access_token');
    setUser(null);
  };

  return <AuthContext.Provider value={{ user, setUser, signIn, signOut, loading }}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
