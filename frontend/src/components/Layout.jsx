import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { logout } from '../api/endpoints';

const NAV = [
  { path:'/dashboard', icon:'🏠', label:'Dashboard' },
  { path:'/progress',  icon:'📈', label:'Progress' },
  { path:'/rewards',   icon:'🏅', label:'Rewards' },
  { path:'/safety',    icon:'🛡️', label:'Safety Layer' },
];

export default function Layout({ children }) {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const { pathname } = useLocation();

  const handleLogout = async () => { try { await logout(); } finally { signOut(); navigate('/login'); } };

  return (
    <div style={styles.app}>
      <nav style={styles.nav}>
        <div style={styles.logo}>Fit<span style={{ color:'#00ff88' }}>Core</span> AI</div>
        <div style={styles.tabs}>
          {NAV.map(n => (
            <button key={n.path} style={{ ...styles.tab, ...(pathname===n.path ? styles.tabActive : {}) }} onClick={() => navigate(n.path)}>
              {n.icon} {n.label}
            </button>
          ))}
        </div>
        <div style={styles.userArea}>
          <div style={styles.avatar}>{user?.name?.[0]?.toUpperCase()}</div>
          <span style={{ fontSize:12, color:'#6b8599' }}>{user?.name}</span>
          <button style={styles.logoutBtn} onClick={handleLogout}>Sign out</button>
        </div>
      </nav>
      <div style={styles.body}>
        <aside style={styles.sidebar}>
          <div style={styles.profileCard}>
            <div style={styles.profileName}>{user?.name}</div>
            <div style={styles.profileMeta}>{user?.goal?.replace('-',' ')} · {user?.gender}</div>
            <div style={styles.bmiRow}>
              <div style={styles.bmiChip}><div style={{ ...styles.bmiVal, color: user?.bmi > 30 ? '#ff6b35' : '#00e5ff' }}>{user?.bmi}</div><div style={styles.bmiLbl}>BMI</div></div>
              <div style={styles.bmiChip}><div style={{ ...styles.bmiVal, color:'#00ff88' }}>{user?.rfm}%</div><div style={styles.bmiLbl}>RFM</div></div>
            </div>
          </div>
          <div style={styles.sidebarSection}>Navigation</div>
          {NAV.map(n => (
            <div key={n.path} style={{ ...styles.sidebarItem, ...(pathname===n.path ? styles.sidebarActive : {}) }} onClick={() => navigate(n.path)}>
              <span>{n.icon}</span>{n.label}
            </div>
          ))}
          <div style={styles.sidebarSection}>Account</div>
          <div style={styles.sidebarItem} onClick={handleLogout}><span>🚪</span>Sign Out</div>
        </aside>
        <main style={styles.main}>{children}</main>
      </div>
    </div>
  );
}

const styles = {
  app:           { minHeight:'100vh', background:'#080c10', color:'#e8f4f8', fontFamily:'monospace' },
  nav:           { display:'flex', alignItems:'center', justifyContent:'space-between', padding:'14px 28px', borderBottom:'1px solid #1f2d3d', background:'rgba(8,12,16,0.95)', position:'sticky', top:0, zIndex:100 },
  logo:          { fontFamily:'sans-serif', fontWeight:800, fontSize:18, color:'#00e5ff' },
  tabs:          { display:'flex', gap:4 },
  tab:           { padding:'7px 14px', borderRadius:6, fontSize:12, cursor:'pointer', border:'1px solid transparent', background:'none', color:'#6b8599', transition:'all 0.2s' },
  tabActive:     { color:'#00e5ff', borderColor:'#00e5ff', background:'rgba(0,229,255,0.05)' },
  userArea:      { display:'flex', alignItems:'center', gap:10 },
  avatar:        { width:32, height:32, borderRadius:'50%', background:'linear-gradient(135deg,#00e5ff,#c084fc)', display:'flex', alignItems:'center', justifyContent:'center', fontFamily:'sans-serif', fontWeight:700, fontSize:13, color:'#000' },
  logoutBtn:     { padding:'6px 12px', background:'transparent', border:'1px solid #1f2d3d', borderRadius:6, color:'#6b8599', cursor:'pointer', fontSize:11 },
  body:          { display:'grid', gridTemplateColumns:'240px 1fr', minHeight:'calc(100vh - 57px)' },
  sidebar:       { borderRight:'1px solid #1f2d3d', padding:'20px 14px', background:'#0e1318' },
  profileCard:   { background:'#141c24', border:'1px solid #1f2d3d', borderRadius:12, padding:16, marginBottom:12 },
  profileName:   { fontFamily:'sans-serif', fontWeight:700, fontSize:15, marginBottom:3 },
  profileMeta:   { fontSize:11, color:'#6b8599', marginBottom:12, textTransform:'capitalize' },
  bmiRow:        { display:'flex', gap:8 },
  bmiChip:       { flex:1, background:'#1c2733', borderRadius:6, padding:8, textAlign:'center' },
  bmiVal:        { fontFamily:'sans-serif', fontWeight:800, fontSize:18 },
  bmiLbl:        { fontSize:9, color:'#6b8599', textTransform:'uppercase', letterSpacing:1 },
  sidebarSection:{ fontSize:10, color:'#6b8599', letterSpacing:2, textTransform:'uppercase', padding:'12px 10px 6px' },
  sidebarItem:   { display:'flex', alignItems:'center', gap:10, padding:'9px 10px', borderRadius:8, cursor:'pointer', fontSize:13, color:'#6b8599', transition:'all 0.15s' },
  sidebarActive: { color:'#00e5ff', background:'rgba(0,229,255,0.06)', borderLeft:'2px solid #00e5ff' },
  main:          { padding:'28px 32px', overflowY:'auto' },
};
