import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { getAvailableBadges, getRewards, getLeaderboard } from '../api/endpoints';

export default function Rewards() {
  const { user }                    = useAuth();
  const [badges, setBadges]         = useState([]);
  const [rewards, setRewards]       = useState({ total_points: 0, streak: 0 });
  const [leaderboard, setLeaderboard] = useState([]);
  const [tab, setTab]               = useState('badges');
  const [loading, setLoading]       = useState(true);

  useEffect(() => {
    if (!user) return;
    Promise.all([
      getAvailableBadges(user.id),
      getRewards(user.id),
      getLeaderboard(),
    ]).then(([br, rr, lr]) => {
      setBadges(br.data);
      setRewards(rr.data);
      setLeaderboard(lr.data);
    }).finally(() => setLoading(false));
  }, [user]);

  if (loading) return <div style={{ color: '#6b8599', padding: 40, textAlign: 'center' }}>Loading rewards...</div>;

  const earned = badges.filter(b => b.earned);
  const locked = badges.filter(b => !b.earned);

  return (
    <div>
      <div style={styles.header}>
        <h1 style={styles.title}>Rewards & Gamification</h1>
        <p style={styles.sub}>Stay consistent to unlock badges and climb the leaderboard</p>
      </div>

      {/* Points hero */}
      <div style={styles.hero}>
        <div>
          <div style={styles.pts}>{rewards.total_points}</div>
          <div style={styles.ptsLabel}>Total Points Earned</div>
          <div style={{ color: '#6b8599', fontSize: 12, marginTop: 6 }}>
            +10 pts per session · +10 bonus for effort ≥7 · +50 for 7-day streak
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={styles.streak}>{rewards.streak || 0}🔥</div>
          <div style={{ color: '#6b8599', fontSize: 13 }}>Day Streak</div>
          <div style={styles.badgeCount}>{earned.length}/{badges.length} badges</div>
        </div>
      </div>

      {/* Progress bar */}
      <div style={styles.progressWrap}>
        <div style={styles.progressTrack}>
          <div style={{ ...styles.progressFill, width: `${badges.length ? (earned.length / badges.length) * 100 : 0}%` }} />
        </div>
        <div style={{ fontSize: 11, color: '#6b8599', marginTop: 6 }}>
          {Math.round(badges.length ? (earned.length / badges.length) * 100 : 0)}% badge completion
        </div>
      </div>

      {/* Tabs */}
      <div style={styles.tabs}>
        {[['badges', '🏅 Badges'], ['leaderboard', '🏆 Leaderboard']].map(([id, label]) => (
          <button key={id} style={{ ...styles.tab, ...(tab === id ? styles.tabActive : {}) }} onClick={() => setTab(id)}>
            {label}
          </button>
        ))}
      </div>

      {/* Badges tab */}
      {tab === 'badges' && (
        <>
          {earned.length > 0 && (
            <>
              <div style={styles.sectionTitle}>✅ Earned ({earned.length})</div>
              <div style={styles.badgeGrid}>
                {earned.map(b => (
                  <div key={b.id} style={styles.badgeEarned}>
                    <div style={styles.badgeIcon}>{b.icon}</div>
                    <div style={styles.badgeName}>{b.name}</div>
                    <div style={styles.badgeDesc}>{b.desc}</div>
                    <div style={styles.badgePts}>+{b.points} pts</div>
                    <div style={styles.earnedLabel}>✓ Earned</div>
                  </div>
                ))}
              </div>
            </>
          )}
          {locked.length > 0 && (
            <>
              <div style={{ ...styles.sectionTitle, marginTop: 24 }}>🔒 Locked ({locked.length})</div>
              <div style={styles.badgeGrid}>
                {locked.map(b => (
                  <div key={b.id} style={styles.badgeLocked}>
                    <div style={{ ...styles.badgeIcon, filter: 'grayscale(1)', opacity: 0.4 }}>{b.icon}</div>
                    <div style={{ ...styles.badgeName, color: '#6b8599' }}>{b.name}</div>
                    <div style={styles.badgeDesc}>{b.desc}</div>
                    <div style={{ ...styles.badgePts, color: '#6b8599' }}>+{b.points} pts</div>
                  </div>
                ))}
              </div>
            </>
          )}
        </>
      )}

      {/* Leaderboard tab */}
      {tab === 'leaderboard' && (
        <div style={styles.leaderboard}>
          {leaderboard.map((entry) => (
            <div key={entry.rank} style={{
              ...styles.lbRow,
              ...(entry.is_me ? styles.lbRowMe : {}),
            }}>
              <div style={styles.lbRank}>
                {entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : entry.rank === 3 ? '🥉' : `#${entry.rank}`}
              </div>
              <div style={styles.lbName}>
                {entry.name}
                {entry.is_me && <span style={styles.youTag}> You</span>}
              </div>
              <div style={styles.lbStats}>
                <span style={{ color: '#00e5ff' }}>{entry.points} pts</span>
                <span style={{ color: '#ff6b35', marginLeft: 16 }}>{entry.streak}🔥</span>
                <span style={{ color: '#c084fc', marginLeft: 16 }}>{entry.badges} badges</span>
              </div>
            </div>
          ))}
          {leaderboard.length === 0 && (
            <div style={{ color: '#6b8599', textAlign: 'center', padding: 40, fontSize: 13 }}>
              No leaderboard data yet. Log workouts to appear here.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

const styles = {
  header:       { marginBottom: 28 },
  title:        { fontFamily: 'sans-serif', fontWeight: 800, fontSize: 26, color: '#e8f4f8', marginBottom: 4 },
  sub:          { color: '#6b8599', fontSize: 13 },
  hero:         { background: 'linear-gradient(135deg,rgba(0,229,255,0.07),rgba(192,132,252,0.07))', border: '1px solid #1f2d3d', borderRadius: 20, padding: 32, display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
  pts:          { fontFamily: 'sans-serif', fontWeight: 800, fontSize: 56, color: '#00e5ff', lineHeight: 1 },
  ptsLabel:     { color: '#6b8599', fontSize: 14, marginTop: 4 },
  streak:       { fontFamily: 'sans-serif', fontWeight: 800, fontSize: 48, color: '#ff6b35', lineHeight: 1 },
  badgeCount:   { color: '#c084fc', fontSize: 13, marginTop: 6 },
  progressWrap: { marginBottom: 24 },
  progressTrack:{ height: 6, background: '#1c2733', borderRadius: 3, overflow: 'hidden' },
  progressFill: { height: '100%', background: 'linear-gradient(90deg,#00e5ff,#00ff88)', borderRadius: 3, transition: 'width 1s ease' },
  tabs:         { display: 'flex', gap: 8, marginBottom: 24 },
  tab:          { padding: '9px 20px', borderRadius: 8, fontSize: 13, cursor: 'pointer', border: '1px solid #1f2d3d', background: 'transparent', color: '#6b8599', transition: 'all 0.2s' },
  tabActive:    { borderColor: '#00e5ff', color: '#00e5ff', background: 'rgba(0,229,255,0.06)' },
  sectionTitle: { fontFamily: 'sans-serif', fontWeight: 700, fontSize: 14, color: '#e8f4f8', marginBottom: 14 },
  badgeGrid:    { display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12 },
  badgeEarned:  { background: '#0e1318', border: '1px solid #00ff88', borderRadius: 14, padding: 18, textAlign: 'center', background: 'rgba(0,255,136,0.04)' },
  badgeLocked:  { background: '#0e1318', border: '1px solid #1f2d3d', borderRadius: 14, padding: 18, textAlign: 'center', opacity: 0.6 },
  badgeIcon:    { fontSize: 32, marginBottom: 8 },
  badgeName:    { fontFamily: 'sans-serif', fontWeight: 700, fontSize: 13, color: '#e8f4f8', marginBottom: 4 },
  badgeDesc:    { fontSize: 11, color: '#6b8599', lineHeight: 1.4, marginBottom: 8 },
  badgePts:     { fontSize: 11, color: '#00ff88', fontWeight: 600 },
  earnedLabel:  { fontSize: 10, color: '#00ff88', marginTop: 6, textTransform: 'uppercase', letterSpacing: 1 },
  leaderboard:  { background: '#0e1318', border: '1px solid #1f2d3d', borderRadius: 16, overflow: 'hidden' },
  lbRow:        { display: 'flex', alignItems: 'center', padding: '16px 20px', borderBottom: '1px solid #1f2d3d', transition: 'background 0.15s' },
  lbRowMe:      { background: 'rgba(0,229,255,0.05)', borderLeft: '3px solid #00e5ff' },
  lbRank:       { width: 40, fontFamily: 'sans-serif', fontWeight: 800, fontSize: 18, color: '#e8f4f8' },
  lbName:       { flex: 1, fontFamily: 'sans-serif', fontWeight: 600, fontSize: 14, color: '#e8f4f8' },
  youTag:       { fontSize: 10, background: 'rgba(0,229,255,0.15)', color: '#00e5ff', padding: '2px 6px', borderRadius: 4, marginLeft: 8 },
  lbStats:      { fontSize: 13 },
};
