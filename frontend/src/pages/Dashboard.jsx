import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import { getRecommendations, createLog, getRewards } from '../api/endpoints';
import { intensityColor } from '../utils/helpers';

export default function Dashboard() {
  const { user, setUser }       = useAuth();
  const [recs, setRecs]         = useState([]);
  const [mode, setMode]         = useState('');
  const [adaptation, setAdapt]  = useState('maintain');
  const [logModal, setLogModal] = useState(null);
  const [effort, setEffort]     = useState(5);
  const [hr, setHr]             = useState(120);
  const [logged, setLogged]     = useState(new Set());
  const [toast, setToast]       = useState(null);
  const [rewards, setRewards]   = useState({ total_points: 0, streak: 0, badges: [] });
  const [loading, setLoading]   = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const showToast = useCallback((msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 4000);
  }, []);

  const loadData = useCallback(async () => {
    if (!user) return;
    try {
      const [recRes, rwRes] = await Promise.all([
        getRecommendations(user.id),
        getRewards(user.id),
      ]);
      setRecs(recRes.data.results || []);
      setMode(recRes.data.mode);
      setAdapt(recRes.data.adaptation);
      setRewards(rwRes.data);
    } catch (e) {
      showToast('Failed to load recommendations', 'error');
    } finally {
      setLoading(false);
    }
  }, [user, showToast]);

  useEffect(() => { loadData(); }, [loadData]);

  const submitLog = async (completed) => {
    if (!logModal || submitting) return;
    setSubmitting(true);
    try {
      const res = await createLog({
        exercise_id:      logModal.exercise.id,
        duration_mins:    30,
        completed,
        perceived_effort: effort,
        heart_rate_avg:   hr,
      });

      setLogged(p => new Set([...p, logModal.exercise.id]));

      // Show HR warning if present
      if (res.data.hr_warning) {
        showToast(res.data.hr_warning, 'warning');
      } else if (completed) {
        showToast(`✅ +${res.data.points_earned} pts · Streak: ${res.data.new_streak} days 🔥`);
      } else {
        showToast('📝 Session logged. Keep going!');
      }

      // Refresh rewards
      const rwRes = await getRewards(user.id);
      setRewards(rwRes.data);
      setLogModal(null);
    } catch (e) {
      showToast('Failed to log session', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const adaptColor = adaptation === 'increase' ? '#00ff88' : adaptation === 'decrease' ? '#ff6b35' : '#00e5ff';
  const adaptIcon  = adaptation === 'increase' ? '↑' : adaptation === 'decrease' ? '↓' : '→';

  if (loading) return (
    <div style={styles.loading}>
      <div style={styles.spinner}>⟳</div>
      <div>Loading your personalised recommendations...</div>
    </div>
  );

  return (
    <div>
      {/* Page header */}
      <div style={styles.header}>
        <h1 style={styles.title}>Today's Recommendations</h1>
        <div style={styles.subRow}>
          <span style={styles.modeBadge}>{mode}</span>
          <span style={{ color: adaptColor, fontSize: 13 }}>
            {adaptIcon} RNN Signal: <strong>{adaptation.toUpperCase()}</strong>
          </span>
          {mode === 'cold-start' && (
            <span style={styles.coldStart}>Log 5 workouts to unlock full Hybrid mode</span>
          )}
        </div>
      </div>

      {/* Stats row */}
      <div style={styles.statsRow}>
        {[
          ['Points',    rewards.total_points,         '#00e5ff'],
          ['Streak',    `${rewards.streak || 0} 🔥`,  '#ff6b35'],
          ['Badges',    rewards.badges?.length || 0,  '#c084fc'],
          ['Sessions',  logged.size,                  '#00ff88'],
        ].map(([label, val, color]) => (
          <div key={label} style={styles.stat}>
            <div style={styles.statLabel}>{label}</div>
            <div style={{ ...styles.statVal, color }}>{val}</div>
          </div>
        ))}
      </div>

      {/* Recommendation cards */}
      <div style={styles.sectionHeader}>
        <span style={styles.sectionTitle}>🤖 AI-Powered Recommendations</span>
        <span style={styles.sectionMeta}>{recs.length} exercises · Sorted by hybrid score</span>
      </div>

      {recs.length === 0 ? (
        <div style={styles.empty}>
          No recommendations available. Your safety profile may be very restrictive.
          Try relaxing some conditions in your profile settings.
        </div>
      ) : (
        <div style={styles.recGrid}>
          {recs.map((r) => {
            const isLogged = logged.has(r.exercise.id);
            return (
              <div
                key={r.exercise.id}
                style={{ ...styles.recCard, ...(isLogged ? styles.recLogged : {}) }}
              >
                {/* Card header */}
                <div style={styles.recTop}>
                  <span style={{ fontSize: 28 }}>{r.exercise.icon}</span>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
                    <span style={{
                      ...styles.sourceBadge,
                      background: r.source === 'ontology' ? 'rgba(255,107,53,0.15)' :
                                  r.source === 'rnn'      ? 'rgba(192,132,252,0.15)' :
                                                            'rgba(0,229,255,0.1)',
                      color: r.source === 'ontology' ? '#ff6b35' :
                             r.source === 'rnn'      ? '#c084fc' : '#00e5ff',
                    }}>
                      {r.source === 'ontology' ? '🛡 Safety' :
                       r.source === 'rnn'      ? '🧠 RNN'    : '⚡ Hybrid'}
                    </span>
                    <span style={{ fontSize: 18, fontWeight: 800, color: '#00e5ff', fontFamily: 'sans-serif' }}>
                      {Math.round(r.final_score * 100)}
                    </span>
                  </div>
                </div>

                {/* Exercise info */}
                <div style={styles.recName}>{r.exercise.name}</div>
                <div style={styles.recMeta}>
                  {r.exercise.category} ·{' '}
                  <span style={{ color: intensityColor(r.exercise.intensity_level) }}>
                    {r.exercise.intensity_level}
                  </span>
                  {' '}· MET {r.exercise.met_value}
                </div>

                {/* Score bars */}
                <div style={styles.bars}>
                  {[
                    ['Content',   r.content_score,   '#00e5ff'],
                    ['Collab',    r.collab_score,     '#00ff88'],
                    ['Adherence', r.adherence_score,  '#ff6b35'],
                  ].map(([label, score, color]) => (
                    <div key={label} style={styles.barRow}>
                      <span style={styles.barLabel}>{label}</span>
                      <div style={styles.barTrack}>
                        <div style={{ ...styles.barFill, width: `${score * 100}%`, background: color }} />
                      </div>
                      <span style={styles.barScore}>{Math.round(score * 100)}%</span>
                    </div>
                  ))}
                </div>

                {/* Action button */}
                {isLogged ? (
                  <div style={styles.loggedLabel}>✓ Logged today</div>
                ) : (
                  <button
                    style={styles.btnLog}
                    onClick={() => { setLogModal(r); setEffort(5); setHr(120); }}
                  >
                    + Log Session
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Log modal */}
      {logModal && (
        <div style={styles.overlay} onClick={() => setLogModal(null)}>
          <div style={styles.modal} onClick={e => e.stopPropagation()}>
            <div style={styles.modalTitle}>
              {logModal.exercise.icon} {logModal.exercise.name}
            </div>
            <div style={styles.modalSub}>
              {logModal.exercise.category} · {logModal.exercise.intensity_level} ·
              Est. {Math.round(logModal.exercise.met_value * (user?.weight_kg || 70) * 0.5)} kcal
            </div>

            {/* Effort slider */}
            <div style={styles.sliderWrap}>
              <div style={styles.sliderRow}>
                <span>Perceived Effort</span>
                <span style={{ color: '#00e5ff', fontWeight: 700 }}>{effort}/10</span>
              </div>
              <input type="range" min={1} max={10} value={effort}
                onChange={e => setEffort(+e.target.value)}
                style={{ width: '100%', accentColor: '#00e5ff' }} />
              <div style={styles.sliderHint}>
                {effort <= 3 ? 'Easy — try harder next time' :
                 effort <= 6 ? 'Moderate — good zone' :
                 effort <= 8 ? 'Hard — excellent effort!' :
                               'Maximum — outstanding!'}
              </div>
            </div>

            {/* Heart rate slider */}
            <div style={styles.sliderWrap}>
              <div style={styles.sliderRow}>
                <span>Avg Heart Rate</span>
                <span style={{ color: '#00e5ff', fontWeight: 700 }}>{hr} bpm</span>
              </div>
              <input type="range" min={60} max={190} value={hr}
                onChange={e => setHr(+e.target.value)}
                style={{ width: '100%', accentColor: '#00e5ff' }} />
              {user?.age && hr >= (220 - user.age) * 0.9 && (
                <div style={{ ...styles.sliderHint, color: '#ff6b35' }}>
                  ⚠️ Near your maximum safe HR ({220 - user.age} bpm)
                </div>
              )}
            </div>

            {/* Adherence prediction */}
            <div style={styles.predBox}>
              <span>AI completion prediction:</span>
              <span style={{ color: '#00ff88', fontWeight: 700 }}>
                {Math.round(logModal.adherence_score * 100)}%
              </span>
            </div>

            <div style={styles.modalBtns}>
              <button style={styles.btnCancel} onClick={() => setLogModal(null)}>Cancel</button>
              <button style={{ ...styles.btnSubmit, background: '#ff4757' }}
                onClick={() => submitLog(false)} disabled={submitting}>
                Incomplete
              </button>
              <button style={styles.btnSubmit}
                onClick={() => submitLog(true)} disabled={submitting}>
                {submitting ? '...' : '✓ Completed!'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div style={{
          ...styles.toast,
          borderColor: toast.type === 'error'   ? '#ff4757' :
                       toast.type === 'warning' ? '#ffa502' : '#00ff88',
        }}>
          {toast.msg}
        </div>
      )}
    </div>
  );
}

const styles = {
  loading:      { color: '#6b8599', padding: 60, textAlign: 'center', fontSize: 14 },
  spinner:      { fontSize: 32, marginBottom: 12, animation: 'spin 1s linear infinite' },
  header:       { marginBottom: 24 },
  title:        { fontFamily: 'sans-serif', fontWeight: 800, fontSize: 26, color: '#e8f4f8', marginBottom: 8 },
  subRow:       { display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' },
  modeBadge:    { fontSize: 11, padding: '3px 10px', borderRadius: 4, background: 'rgba(0,229,255,0.1)', color: '#00e5ff', border: '1px solid rgba(0,229,255,0.2)', textTransform: 'uppercase', letterSpacing: 1 },
  coldStart:    { fontSize: 12, color: '#ff6b35', background: 'rgba(255,107,53,0.1)', padding: '3px 10px', borderRadius: 4 },
  statsRow:     { display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14, marginBottom: 24 },
  stat:         { background: '#0e1318', border: '1px solid #1f2d3d', borderRadius: 12, padding: 18 },
  statLabel:    { fontSize: 11, color: '#6b8599', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 },
  statVal:      { fontFamily: 'sans-serif', fontWeight: 800, fontSize: 26 },
  sectionHeader:{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  sectionTitle: { fontFamily: 'sans-serif', fontWeight: 700, fontSize: 16, color: '#e8f4f8' },
  sectionMeta:  { fontSize: 12, color: '#6b8599' },
  empty:        { background: '#0e1318', border: '1px solid #1f2d3d', borderRadius: 12, padding: 32, textAlign: 'center', color: '#6b8599', fontSize: 13 },
  recGrid:      { display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14 },
  recCard:      { background: '#0e1318', border: '1px solid #1f2d3d', borderRadius: 14, padding: 20, transition: 'border-color 0.2s' },
  recLogged:    { borderColor: '#00ff88', background: 'rgba(0,255,136,0.03)' },
  recTop:       { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 },
  sourceBadge:  { fontSize: 9, padding: '3px 8px', borderRadius: 4, fontWeight: 600, letterSpacing: 1, textTransform: 'uppercase' },
  recName:      { fontFamily: 'sans-serif', fontWeight: 700, fontSize: 15, color: '#e8f4f8', marginBottom: 4 },
  recMeta:      { fontSize: 11, color: '#6b8599', marginBottom: 14 },
  bars:         { display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 14 },
  barRow:       { display: 'flex', alignItems: 'center', gap: 8, fontSize: 10, color: '#6b8599' },
  barLabel:     { width: 65, flexShrink: 0 },
  barTrack:     { flex: 1, height: 4, background: '#1c2733', borderRadius: 2, overflow: 'hidden' },
  barFill:      { height: '100%', borderRadius: 2 },
  barScore:     { width: 32, textAlign: 'right' },
  btnLog:       { width: '100%', padding: 9, background: 'transparent', border: '1px solid #1f2d3d', borderRadius: 8, color: '#6b8599', cursor: 'pointer', fontSize: 12, transition: 'all 0.2s' },
  loggedLabel:  { paddingTop: 14, borderTop: '1px solid #1f2d3d', textAlign: 'center', color: '#00ff88', fontSize: 12 },
  overlay:      { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.75)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(4px)' },
  modal:        { background: '#0e1318', border: '1px solid #1f2d3d', borderRadius: 20, padding: 28, width: 420, maxWidth: '95vw' },
  modalTitle:   { fontFamily: 'sans-serif', fontWeight: 800, fontSize: 20, color: '#e8f4f8', marginBottom: 4 },
  modalSub:     { color: '#6b8599', fontSize: 12, marginBottom: 24 },
  sliderWrap:   { marginBottom: 20 },
  sliderRow:    { display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#6b8599', marginBottom: 8 },
  sliderHint:   { fontSize: 11, color: '#6b8599', marginTop: 6, textAlign: 'center' },
  predBox:      { display: 'flex', justifyContent: 'space-between', background: '#141c24', borderRadius: 8, padding: '10px 14px', fontSize: 12, color: '#6b8599', marginBottom: 20 },
  modalBtns:    { display: 'flex', gap: 8 },
  btnCancel:    { flex: 1, padding: 12, background: 'transparent', border: '1px solid #1f2d3d', borderRadius: 10, color: '#6b8599', cursor: 'pointer', fontSize: 12 },
  btnSubmit:    { flex: 2, padding: 12, background: '#00ff88', border: 'none', borderRadius: 10, color: '#000', fontFamily: 'sans-serif', fontWeight: 700, fontSize: 14, cursor: 'pointer' },
  toast:        { position: 'fixed', bottom: 24, right: 24, background: '#0e1318', border: '1px solid #00ff88', borderRadius: 12, padding: '14px 20px', color: '#e8f4f8', fontSize: 13, zIndex: 999, maxWidth: 380, lineHeight: 1.5 },
};
