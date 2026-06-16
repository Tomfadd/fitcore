import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { register } from '../api/endpoints';
import { useAuth } from '../hooks/useAuth';
import { calcBMI, calcRFM, bmiCategory } from '../utils/helpers';

const CONDITIONS = [
  ['obesity',       'Obesity (BMI > 30)'],
  ['hypertension',  'Hypertension'],
  ['diabetes',      'Type 2 Diabetes'],
  ['joint-pain',    'Joint Pain'],
  ['elderly',       'Elderly (65+)'],
  ['back-pain',     'Back Pain'],
];

export default function Register() {
  const { signIn } = useAuth();
  const navigate   = useNavigate();
  const [form, setForm]       = useState({ name:'', email:'', password:'', age:'', gender:'male', weight_kg:'', height_cm:'', goal:'weight-loss', conditions:[] });
  const [computed, setComputed] = useState(null);
  const [error, setError]     = useState('');
  const [loading, setLoading] = useState(false);

  const set = (k, v) => setForm(p => ({ ...p, [k]: v }));
  const toggleCond = (k) => setForm(p => ({ ...p, conditions: p.conditions.includes(k) ? p.conditions.filter(c => c !== k) : [...p.conditions, k] }));

  useEffect(() => {
    if (form.weight_kg && form.height_cm) {
      const bmi = parseFloat(calcBMI(form.weight_kg, form.height_cm));
      const rfm = parseFloat(calcRFM(form.weight_kg, form.height_cm, form.gender));
      setComputed({ bmi, rfm });
    }
  }, [form.weight_kg, form.height_cm, form.gender]);

  const submit = async () => {
    setError(''); setLoading(true);
    try {
      const { data } = await register({ ...form, age: +form.age, weight_kg: +form.weight_kg, height_cm: +form.height_cm });
      const { getMe } = await import('../api/endpoints');
      const user = await getMe();
      signIn(data.access_token, user.data);
      navigate('/dashboard');
    } catch (e) {
      setError(e.response?.data?.detail || 'Registration failed');
    } finally { setLoading(false); }
  };

  const cat = computed ? bmiCategory(computed.bmi) : null;

  return (
    <div style={styles.wrap}>
      <div style={styles.card}>
        <h1 style={styles.title}>Join <span style={{ color: '#00e5ff' }}>FitCore AI</span></h1>
        <p style={styles.sub}>Complete your health profile to activate personalised recommendations</p>

        {error && <div style={styles.error}>{error}</div>}

        <div style={styles.grid}>
          <div style={styles.field}>
            <label style={styles.label}>Full Name</label>
            <input style={styles.input} placeholder="e.g. Alex Johnson" value={form.name} onChange={e => set('name', e.target.value)} />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Email</label>
            <input style={styles.input} type="email" placeholder="you@email.com" value={form.email} onChange={e => set('email', e.target.value)} />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Password</label>
            <input style={styles.input} type="password" placeholder="Min 8 characters" value={form.password} onChange={e => set('password', e.target.value)} />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Age</label>
            <input style={styles.input} type="number" placeholder="e.g. 28" value={form.age} onChange={e => set('age', e.target.value)} />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Gender</label>
            <select style={styles.input} value={form.gender} onChange={e => set('gender', e.target.value)}>
              <option value="male">Male</option>
              <option value="female">Female</option>
            </select>
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Weight (kg)</label>
            <input style={styles.input} type="number" placeholder="e.g. 82" value={form.weight_kg} onChange={e => set('weight_kg', e.target.value)} />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Height (cm)</label>
            <input style={styles.input} type="number" placeholder="e.g. 175" value={form.height_cm} onChange={e => set('height_cm', e.target.value)} />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Fitness Goal</label>
            <select style={styles.input} value={form.goal} onChange={e => set('goal', e.target.value)}>
              <option value="weight-loss">Weight Loss</option>
              <option value="strength">Build Strength</option>
              <option value="endurance">Endurance</option>
              <option value="flexibility">Flexibility</option>
            </select>
          </div>
        </div>

        {computed && (
          <div style={styles.bmiRow}>
            <div style={styles.bmiChip}><div style={{ ...styles.bmiVal, color: cat.color }}>{computed.bmi}</div><div style={styles.bmiLbl}>BMI</div></div>
            <div style={styles.bmiChip}><div style={{ ...styles.bmiVal, color: '#00ff88' }}>{computed.rfm}%</div><div style={styles.bmiLbl}>Rel. Fat Mass</div></div>
            <div style={styles.bmiChip}><div style={{ ...styles.bmiVal, fontSize: 14, color: cat.color }}>{cat.label}</div><div style={styles.bmiLbl}>Category</div></div>
          </div>
        )}

        <div style={{ marginTop: 20 }}>
          <div style={styles.label}>Health Conditions (activates SWRL safety rules)</div>
          <div style={styles.condGrid}>
            {CONDITIONS.map(([k, label]) => (
              <div key={k} style={{ ...styles.cond, ...(form.conditions.includes(k) ? styles.condActive : {}) }} onClick={() => toggleCond(k)}>
                {form.conditions.includes(k) ? '☑ ' : '☐ '}{label}
              </div>
            ))}
          </div>
        </div>

        {(computed?.bmi > 35 || form.conditions.length >= 2) && (
          <div style={styles.warning}>⚠️ High-risk profile detected. Safety layer will be fully active — all high-intensity exercises will be blocked.</div>
        )}

        <button style={styles.btn} onClick={submit} disabled={loading}>{loading ? 'Activating...' : 'Activate AI System →'}</button>
        <p style={{ textAlign: 'center', marginTop: 16, fontSize: 12, color: '#6b8599' }}>
          Already registered? <span style={{ color: '#00e5ff', cursor: 'pointer' }} onClick={() => navigate('/login')}>Sign in</span>
        </p>
      </div>
    </div>
  );
}

const styles = {
  wrap:      { minHeight: '100vh', background: '#080c10', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 },
  card:      { width: '100%', maxWidth: 560, background: '#0e1318', border: '1px solid #1f2d3d', borderRadius: 20, padding: 32 },
  title:     { fontFamily: 'sans-serif', fontWeight: 800, fontSize: 28, color: '#e8f4f8', marginBottom: 6 },
  sub:       { color: '#6b8599', fontSize: 13, marginBottom: 28, lineHeight: 1.6 },
  error:     { background: 'rgba(255,71,87,0.1)', border: '1px solid #ff4757', borderRadius: 8, padding: '10px 14px', color: '#ff4757', fontSize: 13, marginBottom: 16 },
  grid:      { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 },
  field:     { display: 'flex', flexDirection: 'column', gap: 6 },
  label:     { fontSize: 11, color: '#6b8599', textTransform: 'uppercase', letterSpacing: 1 },
  input:     { background: '#141c24', border: '1px solid #1f2d3d', borderRadius: 8, padding: '10px 14px', color: '#e8f4f8', fontFamily: 'monospace', fontSize: 13, outline: 'none' },
  bmiRow:    { display: 'flex', gap: 8, marginTop: 16 },
  bmiChip:   { flex: 1, background: '#141c24', borderRadius: 8, padding: 10, textAlign: 'center' },
  bmiVal:    { fontWeight: 800, fontSize: 20, color: '#00e5ff' },
  bmiLbl:    { fontSize: 9, color: '#6b8599', textTransform: 'uppercase', letterSpacing: 1 },
  condGrid:  { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 10 },
  cond:      { padding: '10px 14px', background: '#141c24', border: '1px solid #1f2d3d', borderRadius: 8, cursor: 'pointer', fontSize: 12, color: '#6b8599' },
  condActive:{ borderColor: '#ff6b35', color: '#ff6b35', background: 'rgba(255,107,53,0.08)' },
  warning:   { background: 'rgba(255,107,53,0.1)', border: '1px solid #ff6b35', borderRadius: 8, padding: '12px 14px', color: '#ff6b35', fontSize: 12, marginTop: 14, lineHeight: 1.5 },
  btn:       { width: '100%', marginTop: 20, padding: 14, background: '#00e5ff', color: '#000', border: 'none', borderRadius: 10, fontWeight: 800, fontSize: 15, cursor: 'pointer' },
};
