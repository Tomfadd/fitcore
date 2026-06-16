import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, getMe } from '../api/endpoints';
import { useAuth } from '../hooks/useAuth';

export default function Login() {
  const { signIn } = useAuth();
  const navigate   = useNavigate();
  const [form, setForm]     = useState({ email: '', password: '' });
  const [error, setError]   = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setError(''); setLoading(true);
    try {
      const { data } = await login(form);
      const user = await getMe();
      signIn(data.access_token, user.data);
      navigate('/dashboard');
    } catch (e) {
      setError(e.response?.data?.detail || 'Login failed');
    } finally { setLoading(false); }
  };

  return (
    <div style={styles.wrap}>
      <div style={styles.card}>
        <h1 style={styles.title}><span style={{ color: '#00e5ff' }}>FitCore</span> AI</h1>
        <p style={styles.sub}>Sign in to your account</p>
        {error && <div style={styles.error}>{error}</div>}
        <div style={styles.field}><label style={styles.label}>Email</label><input style={styles.input} type="email" value={form.email} onChange={e => setForm(p => ({ ...p, email: e.target.value }))} /></div>
        <div style={{ ...styles.field, marginTop: 14 }}><label style={styles.label}>Password</label><input style={styles.input} type="password" value={form.password} onChange={e => setForm(p => ({ ...p, password: e.target.value }))} onKeyDown={e => e.key === 'Enter' && submit()} /></div>
        <button style={styles.btn} onClick={submit} disabled={loading}>{loading ? 'Signing in...' : 'Sign In'}</button>
        <p style={{ textAlign: 'center', marginTop: 16, fontSize: 12, color: '#6b8599' }}>
          No account? <span style={{ color: '#00e5ff', cursor: 'pointer' }} onClick={() => navigate('/register')}>Register here</span>
        </p>
      </div>
    </div>
  );
}

const styles = {
  wrap:  { minHeight: '100vh', background: '#080c10', display: 'flex', alignItems: 'center', justifyContent: 'center' },
  card:  { width: 380, background: '#0e1318', border: '1px solid #1f2d3d', borderRadius: 20, padding: 36 },
  title: { fontFamily: 'sans-serif', fontWeight: 800, fontSize: 28, color: '#e8f4f8', marginBottom: 6 },
  sub:   { color: '#6b8599', fontSize: 13, marginBottom: 28 },
  error: { background: 'rgba(255,71,87,0.1)', border: '1px solid #ff4757', borderRadius: 8, padding: '10px 14px', color: '#ff4757', fontSize: 13, marginBottom: 16 },
  field: { display: 'flex', flexDirection: 'column', gap: 6 },
  label: { fontSize: 11, color: '#6b8599', textTransform: 'uppercase', letterSpacing: 1 },
  input: { background: '#141c24', border: '1px solid #1f2d3d', borderRadius: 8, padding: '10px 14px', color: '#e8f4f8', fontFamily: 'monospace', fontSize: 13, outline: 'none' },
  btn:   { width: '100%', marginTop: 24, padding: 14, background: '#00e5ff', color: '#000', border: 'none', borderRadius: 10, fontWeight: 800, fontSize: 15, cursor: 'pointer' },
};
