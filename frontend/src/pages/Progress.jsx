import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { getLogs, getLogStats, getMyStats } from '../api/endpoints';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis,
  Tooltip, ResponsiveContainer, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, Legend,
} from 'recharts';

const DAYS = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
const TT = { contentStyle: { background: '#0e1318', border: '1px solid #1f2d3d', borderRadius: 8, color: '#e8f4f8', fontSize: 12 } };

export default function Progress() {
  const { user }              = useAuth();
  const [logs, setLogs]       = useState([]);
  const [stats, setStats]     = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    Promise.all([getLogs(user.id), getLogStats(user.id)])
      .then(([lr, sr]) => { setLogs(lr.data); setStats(sr.data); })
      .finally(() => setLoading(false));
  }, [user]);

  if (loading) return <div style={{ color: '#6b8599', padding: 40, textAlign: 'center' }}>Loading analytics...</div>;

  // Weekly bar chart data
  const weekly = DAYS.map((day, i) => {
    const dayLogs = logs.filter(l => new Date(l.logged_at).getDay() === (i + 1) % 7);
    return {
      day,
      completed: dayLogs.filter(l => l.completed).length,
      calories:  dayLogs.reduce((a, b) => a + (b.calories_burned || 0), 0),
    };
  });

  // Effort trend (last 10)
  const effortTrend = [...logs].reverse().slice(0, 10).reverse().map((l, i) => ({
    session: i + 1,
    effort:  l.perceived_effort || 0,
    hr:      l.heart_rate_avg || 0,
  }));

  // Radar data
  const categoryMap = { Cardio: 0, Strength: 0, Flexibility: 0 };
  // We don't have category on log directly — approximate from effort distribution
  const radarData = [
    { subject: 'Consistency',  value: Math.min((stats?.completion_rate || 0), 100) },
    { subject: 'Intensity',    value: Math.min((stats?.avg_effort || 0) * 10, 100) },
    { subject: 'Volume',       value: Math.min((stats?.total_sessions || 0) * 5, 100) },
    { subject: 'Calorie Burn', value: Math.min((stats?.total_calories || 0) / 50, 100) },
    { subject: 'Streak',       value: Math.min((stats?.current_streak || 0) * 10, 100) },
  ];

  const statCards = [
    ['Sessions',       stats?.total_sessions || 0,                              '#00e5ff'],
    ['Completed',      stats?.completed || 0,                                   '#00ff88'],
    ['Completion %',   `${stats?.completion_rate || 0}%`,                       '#c084fc'],
    ['Calories',       `${stats?.total_calories || 0} kcal`,                    '#ff6b35'],
    ['Avg Effort',     `${stats?.avg_effort || 0}/10`,                          '#00e5ff'],
    ['Total Duration', `${Math.round((stats?.total_duration_mins || 0) / 60)}h`,  '#00ff88'],
  ];

  return (
    <div>
      <div style={styles.header}>
        <h1 style={styles.title}>Progress Analytics</h1>
        <p style={styles.sub}>Your performance data visualised — updated in real time</p>
      </div>

      {/* Stat cards */}
      <div style={styles.statsGrid}>
        {statCards.map(([label, val, color]) => (
          <div key={label} style={styles.statCard}>
            <div style={styles.statLabel}>{label}</div>
            <div style={{ ...styles.statVal, color }}>{val}</div>
          </div>
        ))}
      </div>

      {logs.length === 0 ? (
        <div style={styles.empty}>
          No workout data yet. Log your first session from the Dashboard to see your analytics here.
        </div>
      ) : (
        <div style={styles.chartsGrid}>
          {/* Weekly activity */}
          <div style={{ ...styles.chartCard, gridColumn: '1/-1' }}>
            <div style={styles.chartTitle}>Weekly Activity — Completions & Calories</div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={weekly} barGap={4}>
                <XAxis dataKey="day" tick={{ fill: '#6b8599', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#6b8599', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip {...TT} />
                <Legend wrapperStyle={{ fontSize: 11, color: '#6b8599' }} />
                <Bar dataKey="completed" fill="#00e5ff" radius={[4, 4, 0, 0]} name="Completed" />
                <Bar dataKey="calories"  fill="#00ff88" radius={[4, 4, 0, 0]} name="Calories" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Effort trend */}
          <div style={styles.chartCard}>
            <div style={styles.chartTitle}>Effort & Heart Rate Trend (Last 10)</div>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={effortTrend}>
                <XAxis dataKey="session" tick={{ fill: '#6b8599', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#6b8599', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip {...TT} />
                <Legend wrapperStyle={{ fontSize: 11, color: '#6b8599' }} />
                <Line type="monotone" dataKey="effort" stroke="#c084fc" strokeWidth={2} dot={{ fill: '#c084fc', r: 3 }} name="Effort" />
                <Line type="monotone" dataKey="hr"     stroke="#ff6b35" strokeWidth={2} dot={{ fill: '#ff6b35', r: 3 }} name="HR (÷10)" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Fitness radar */}
          <div style={styles.chartCard}>
            <div style={styles.chartTitle}>Fitness Profile Radar</div>
            <ResponsiveContainer width="100%" height={200}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#1f2d3d" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#6b8599', fontSize: 10 }} />
                <Radar dataKey="value" stroke="#00e5ff" fill="#00e5ff" fillOpacity={0.15} name="You" />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* Completion rate summary */}
          <div style={{ ...styles.chartCard, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
            <div style={styles.chartTitle}>Overall Completion Rate</div>
            <div style={{ fontSize: 64, fontWeight: 800, color: '#00ff88', fontFamily: 'sans-serif', lineHeight: 1 }}>
              {stats?.completion_rate || 0}%
            </div>
            <div style={{ color: '#6b8599', fontSize: 13, marginTop: 8 }}>
              {stats?.completed || 0} of {stats?.total_sessions || 0} sessions completed
            </div>
            <div style={{ marginTop: 16, width: '100%', height: 8, background: '#1c2733', borderRadius: 4, overflow: 'hidden' }}>
              <div style={{ width: `${stats?.completion_rate || 0}%`, height: '100%', background: 'linear-gradient(90deg, #00e5ff, #00ff88)', borderRadius: 4, transition: 'width 1s ease' }} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const styles = {
  header:     { marginBottom: 28 },
  title:      { fontFamily: 'sans-serif', fontWeight: 800, fontSize: 26, color: '#e8f4f8', marginBottom: 4 },
  sub:        { color: '#6b8599', fontSize: 13 },
  statsGrid:  { display: 'grid', gridTemplateColumns: 'repeat(6,1fr)', gap: 12, marginBottom: 24 },
  statCard:   { background: '#0e1318', border: '1px solid #1f2d3d', borderRadius: 12, padding: '16px 14px' },
  statLabel:  { fontSize: 10, color: '#6b8599', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 },
  statVal:    { fontFamily: 'sans-serif', fontWeight: 800, fontSize: 20 },
  empty:      { background: '#0e1318', border: '1px solid #1f2d3d', borderRadius: 12, padding: 40, textAlign: 'center', color: '#6b8599', fontSize: 13 },
  chartsGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 },
  chartCard:  { background: '#0e1318', border: '1px solid #1f2d3d', borderRadius: 16, padding: 24 },
  chartTitle: { fontFamily: 'sans-serif', fontWeight: 700, fontSize: 14, color: '#e8f4f8', marginBottom: 20 },
};
