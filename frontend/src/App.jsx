import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth';
import Layout from './components/Layout';
import Register  from './pages/Register';
import Login     from './pages/Login';
import Dashboard from './pages/Dashboard';
import Progress  from './pages/Progress';
import Rewards   from './pages/Rewards';
import Safety    from './pages/Safety';

function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div style={{ color:'#6b8599', padding:40, textAlign:'center' }}>Loading...</div>;
  return user ? <Layout>{children}</Layout> : <Navigate to="/login" />;
}

function PublicRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  return user ? <Navigate to="/dashboard" /> : children;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" />} />
          <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
          <Route path="/login"    element={<PublicRoute><Login /></PublicRoute>} />
          <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
          <Route path="/progress"  element={<PrivateRoute><Progress /></PrivateRoute>} />
          <Route path="/rewards"   element={<PrivateRoute><Rewards /></PrivateRoute>} />
          <Route path="/safety"    element={<PrivateRoute><Safety /></PrivateRoute>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
