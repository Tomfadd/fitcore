import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { getSafetyRules } from '../api/endpoints';

export default function Safety() {
  const { user }                    = useAuth();
  const [data, setData]             = useState(null);
  const [loading, setLoading]       = useState(true);

  useEffect(() => {
    if (!user) return;
    getSafetyRules(user.id)
      .then(r => setData(r.data))
      .finally(() => setLoading(false));
  }, [user]);

  if (loading) return <div style={styles.loading}>Loading safety profile...</div>;

  const rules           = data?.rules || [];
  const blockedExercises = data?.blocked_exercises || [];
  const activeCount     = data?.active_rule_count || 0;

  return (
    <div>
      <div style={styles.header}>
        <h1 style={styles.title}>Ontology Safety Layer</h1>
        <p style={styles.sub}>
          SWRL rule engine · {activeCount} rule{activeCount !== 1 ? 's' : ''} active for your profile ·
          {blockedExercises.length} exercise{blockedExercises.length !== 1 ? 's' : ''} blocked
        </p>
      </div>

      {/* Explainer */}
      <div style={styles.info}>
        <span style={{ fontSize: 18 }}>🛡️</span>
        <div>
          The safety layer is a <strong>hard veto</strong> — it runs before every recommendation
          and cannot be overridden by any ML model score. Every rule firing is written to the
          safety audit trail for research compliance and clinical accountability.
        </div>
      </div>

      {/* Rule cards */}
      <h2 style={styles.sectionTitle}>SWRL Rules ({rules.length})</h2>
      <div style={styles.ruleGrid}>
        {rules.map(rule => (
          <div
            key={rule.id}
            style={{
              ...styles.ruleCard,
              ...(rule.active ? {
                borderColor: '#ff6b35',
                background: 'rgba(255,107,53,0.05)',
              } : {}),
            }}
          >
            <div style={styles.ruleHeader}>
              <div style={{
                ...styles.dot,
                background:  rule.active ? '#ff6b35' : '#1f2d3d',
                boxShadow:   rule.active ? '0 0 8px #ff6b35' : 'none',
              }} />
              <div>
                <div style={styles.ruleName}>{rule.name}</div>
                <div style={styles.ruleId}>{rule.id}</div>
              </div>
              {rule.active && (
                <span style={styles.activeTag}>ACTIVE</span>
              )}
            </div>
            <div style={styles.ruleBody}>{rule.reason}</div>
            <div style={styles.ruleStatus}>
              {rule.active
                ? <span style={{ color: '#ff6b35' }}>⚡ Enforced on your profile</span>
                : <span style={{ color: '#6b8599' }}>○ Not applicable to your profile</span>
              }
            </div>
          </div>
        ))}
      </div>

      {/* Blocked exercises */}
      {blockedExercises.length > 0 && (
        <>
          <h2 style={{ ...styles.sectionTitle, marginTop: 32 }}>
            🚫 Blocked Exercises ({blockedExercises.length})
          </h2>
          <div style={styles.blockedGrid}>
            {blockedExercises.map(ex => (
              <div key={ex.id} style={styles.blockedCard}>
                <div style={styles.blockedTop}>
                  <span style={{ fontSize: 22 }}>{ex.icon}</span>
                  <span style={styles.blockedRule}>{ex.rule}</span>
                </div>
                <div style={styles.blockedName}>{ex.name}</div>
                <div style={styles.blockedIntensity}>{ex.intensity_level} intensity</div>
                <div style={styles.blockedReason}>{ex.reason}</div>
              </div>
            ))}
          </div>
        </>
      )}

      {activeCount === 0 && (
        <div style={styles.allClear}>
          ✅ No safety restrictions active. You have full access to all exercise intensities.
        </div>
      )}
    </div>
  );
}

const styles = {
  loading:       { color: '#6b8599', padding: 40, textAlign: 'center' },
  header:        { marginBottom: 28 },
  title:         { fontFamily: 'sans-serif', fontWeight: 800, fontSize: 26, color: '#e8f4f8', marginBottom: 4 },
  sub:           { color: '#6b8599', fontSize: 13 },
  info:          { display: 'flex', gap: 14, alignItems: 'flex-start', background: 'rgba(0,229,255,0.05)', border: '1px solid rgba(0,229,255,0.15)', borderRadius: 12, padding: '16px 18px', color: '#e8f4f8', fontSize: 13, lineHeight: 1.6, marginBottom: 28 },
  sectionTitle:  { fontFamily: 'sans-serif', fontWeight: 700, fontSize: 16, color: '#e8f4f8', marginBottom: 16 },
  ruleGrid:      { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 },
  ruleCard:      { background: '#0e1318', border: '1px solid #1f2d3d', borderRadius: 14, padding: 20, transition: 'all 0.2s' },
  ruleHeader:    { display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 12 },
  dot:           { width: 10, height: 10, borderRadius: '50%', flexShrink: 0, marginTop: 4, transition: 'all 0.3s' },
  ruleName:      { fontFamily: 'sans-serif', fontWeight: 700, fontSize: 14, color: '#e8f4f8' },
  ruleId:        { fontSize: 10, color: '#6b8599', marginTop: 2, letterSpacing: 1 },
  activeTag:     { marginLeft: 'auto', fontSize: 9, padding: '3px 8px', background: 'rgba(255,107,53,0.2)', color: '#ff6b35', borderRadius: 4, fontWeight: 700, letterSpacing: 1, flexShrink: 0 },
  ruleBody:      { fontSize: 12, color: '#6b8599', lineHeight: 1.6, marginBottom: 10 },
  ruleStatus:    { fontSize: 11, paddingTop: 10, borderTop: '1px solid #1f2d3d' },
  blockedGrid:   { display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12 },
  blockedCard:   { background: 'rgba(255,71,87,0.05)', border: '1px solid rgba(255,71,87,0.2)', borderRadius: 12, padding: 16 },
  blockedTop:    { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  blockedRule:   { fontSize: 10, padding: '2px 8px', background: 'rgba(255,71,87,0.15)', color: '#ff4757', borderRadius: 4, fontWeight: 700 },
  blockedName:   { fontFamily: 'sans-serif', fontWeight: 700, fontSize: 14, color: '#e8f4f8', marginBottom: 2 },
  blockedIntensity: { fontSize: 11, color: '#ff4757', marginBottom: 6 },
  blockedReason: { fontSize: 11, color: '#6b8599', lineHeight: 1.4 },
  allClear:      { marginTop: 24, padding: 20, background: 'rgba(0,255,136,0.06)', border: '1px solid rgba(0,255,136,0.2)', borderRadius: 12, color: '#00ff88', fontSize: 13 },
};
