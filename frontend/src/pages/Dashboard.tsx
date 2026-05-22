import { useState, useEffect } from 'react'
import { useNavigate, useLocation, Link, Outlet } from 'react-router-dom'
import { getScore, computeScore, acceptOffer } from '../api/intelligence'
import { useAuthStore } from '../store/authStore'
import { useBusinessStore } from '../store/businessStore'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

// ─── Theme ────────────────────────────────────────────────────────────────────
const T = {
  bg:      "#0a0a0f",
  surface: "#0f0f14",
  border:  "#1a1a1a",
  border2: "#222",
  text:    "#f0f0f0",
  textSub: "#888",
  muted:   "#555",
  green:   "#1D9E75",
  greenBg: "rgba(29,158,117,0.10)",
  red:     "#E24B4A",
  yellow:  "#EF9F27",
};

// ─── Sidebar Nav Config ───────────────────────────────────────────────────────
const NAV_ITEMS = [
  { path: "/dashboard",              icon: "◈",  label: "Dashboard"     },
  { path: "/dashboard/invoices",     icon: "⧉",  label: "Invoices"      },
  { path: "/dashboard/score",        icon: "◎",  label: "Credit Score"  },
  { path: "/dashboard/loans",        icon: "⬡",  label: "Loan Offers"   },
  { path: "/dashboard/statements",   icon: "≡",  label: "Financials"    },
  { path: "/dashboard/documents",    icon: "⊞",  label: "Documents"     },
  { path: "/dashboard/profile",      icon: "◉",  label: "Profile"       },
];

// ─── Sidebar ──────────────────────────────────────────────────────────────────
export function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuthStore();
  const [collapsed, setCollapsed] = useState(false);

  const isActive = (path: string) => {
    if (path === "/dashboard") return location.pathname === "/dashboard";
    return location.pathname.startsWith(path);
  };

  return (
    <div style={{
      width: collapsed ? 56 : 200,
      minHeight: "100vh",
      background: T.surface,
      borderRight: `0.5px solid ${T.border}`,
      display: "flex",
      flexDirection: "column",
      transition: "width 0.2s ease",
      flexShrink: 0,
      position: "sticky",
      top: 0,
      zIndex: 100,
    }}>
      {/* Logo + collapse */}
      <div style={{ padding: collapsed ? "1.2rem 0" : "1.2rem 1rem", display: "flex", alignItems: "center", justifyContent: collapsed ? "center" : "space-between", borderBottom: `0.5px solid ${T.border}` }}>
        {!collapsed && (
          <span style={{ fontSize: 12, letterSpacing: "0.12em", color: T.textSub, textTransform: "uppercase", fontWeight: 500 }}>CreditBridge</span>
        )}
        <button onClick={() => setCollapsed(c => !c)} style={{ background: "none", border: "none", cursor: "pointer", color: T.muted, fontSize: 14, padding: 2, lineHeight: 1 }}>
          {collapsed ? "→" : "←"}
        </button>
      </div>

      {/* Nav links */}
      <nav style={{ flex: 1, padding: "0.75rem 0" }}>
        {NAV_ITEMS.map(item => {
          const active = isActive(item.path);
          return (
            <Link key={item.path} to={item.path} style={{ textDecoration: "none" }}>
              <div style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: collapsed ? "10px 0" : "10px 1rem",
                justifyContent: collapsed ? "center" : "flex-start",
                margin: "1px 6px",
                borderRadius: 8,
                background: active ? T.greenBg : "transparent",
                color: active ? T.green : T.textSub,
                fontSize: 13,
                fontWeight: active ? 500 : 400,
                transition: "all 0.15s",
                cursor: "pointer",
                position: "relative",
              }}
                onMouseEnter={e => { if (!active) e.currentTarget.style.background = "rgba(255,255,255,0.03)"; }}
                onMouseLeave={e => { if (!active) e.currentTarget.style.background = "transparent"; }}
              >
                {/* Active indicator */}
                {active && <div style={{ position: "absolute", left: -6, top: "50%", transform: "translateY(-50%)", width: 3, height: 18, background: T.green, borderRadius: 2 }} />}
                <span style={{ fontSize: 15, width: 18, textAlign: "center", flexShrink: 0 }}>{item.icon}</span>
                {!collapsed && <span style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{item.label}</span>}
              </div>
            </Link>
          );
        })}
      </nav>

      {/* Bottom: sign out */}
      <div style={{ borderTop: `0.5px solid ${T.border}`, padding: collapsed ? "0.75rem 0" : "0.75rem 1rem" }}>
        <button onClick={() => { logout(); navigate('/'); }} style={{
          width: "100%", display: "flex", alignItems: "center", gap: 10, justifyContent: collapsed ? "center" : "flex-start",
          background: "none", border: "none", cursor: "pointer", color: T.muted, fontSize: 12, padding: collapsed ? "8px 0" : "8px 0",
        }}>
          <span style={{ fontSize: 14 }}>⎋</span>
          {!collapsed && <span>Sign out</span>}
        </button>
      </div>
    </div>
  );
}

// ─── Shell (Sidebar + Page content) ──────────────────────────────────────────
export function DashboardShell() {
  return (
    <div style={{ display: "flex", minHeight: "100vh", background: T.bg }}>
      <Sidebar />
      <main style={{ flex: 1, overflowY: "auto", minHeight: "100vh" }}>
        <Outlet />
      </main>
    </div>
  );
}

// ─── Cash Flow Data ───────────────────────────────────────────────────────────
const cashFlowData = [
  { month: 'May', credits: 38, debits: 14 },
  { month: 'Jun', credits: 42, debits: 16 },
  { month: 'Jul', credits: 40, debits: 15 },
  { month: 'Aug', credits: 45, debits: 18 },
  { month: 'Sep', credits: 38, debits: 14 },
  { month: 'Oct', credits: 41, debits: 16 },
  { month: 'Nov', credits: 43, debits: 15 },
  { month: 'Dec', credits: 39, debits: 14 },
  { month: 'Jan', credits: 40, debits: 16 },
  { month: 'Feb', credits: 44, debits: 15 },
  { month: 'Mar', credits: 41, debits: 16 },
  { month: 'Apr', credits: 40, debits: 15 },
];

// ─── Dashboard Home Page ──────────────────────────────────────────────────────
export default function Dashboard() {
  const { business_id } = useAuthStore();
  const { scoreData, setScoreData } = useBusinessStore();
  const [loading, setLoading] = useState(!scoreData);
  const [accepting, setAccepting] = useState<string | null>(null);
  const [accepted, setAccepted] = useState<string | null>(null);

  useEffect(() => {
    if (!scoreData && business_id) {
      getScore(business_id)
        .then(r => setScoreData(r.data))
        .catch(() => computeScore(business_id!).then(r => setScoreData(r.data)))
        .finally(() => setLoading(false));
    } else { setLoading(false); }
  }, []);

  const handleAccept = async (offer: any) => {
    setAccepting(offer.lender);
    try {
      await acceptOffer({ business_id: business_id!, lender_name: offer.lender, amount: offer.amount, rate: offer.rate });
      setAccepted(offer.lender);
      alert(`Offer accepted! ${offer.lender} will contact you within 24 hours.`);
    } catch { alert('Something went wrong. Try again.'); }
    finally { setAccepting(null); }
  };

  if (loading) return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: T.muted, fontSize: 13 }}>
      Computing your score...
    </div>
  );

  const score = scoreData!;
  const gradeColor = score.score >= 750 ? T.green : score.score >= 650 ? T.yellow : T.red;

  const subScores = [
    { label: 'Cash flow',            value: score.cash_flow_score || 0 },
    { label: 'Payment discipline',   value: score.payment_discipline_score || 0 },
    { label: 'GST compliance',       value: score.gst_compliance_score || 0 },
    { label: 'Revenue consistency',  value: score.revenue_growth_score || 0 },
    { label: 'Vintage',              value: score.business_vintage_score || 0 },
  ];

  const loanOffers = [
    { lender: 'Lendingkart NBFC', amount: 7500000, rate: 13.5, tenure: 12, featured: true },
    { lender: 'Kotak Mahindra',   amount: 6000000, rate: 14.2, tenure: 12, featured: false },
    { lender: 'HDFC Overdraft',   amount: 5000000, rate: 15.0, tenure: 0,  featured: false },
  ];

  return (
    <div style={{ padding: '1.5rem', maxWidth: 960, margin: '0 auto' }}>

      {/* Quick nav pills (top) */}
      <div style={{ display: "flex", gap: 8, marginBottom: "1.5rem", flexWrap: "wrap" }}>
        {[
          { to: "/dashboard/invoices",   label: "📄 Invoices" },
          { to: "/dashboard/score",      label: "◎ Credit Score" },
          { to: "/dashboard/loans",      label: "⬡ Loan Offers" },
          { to: "/dashboard/statements", label: "≡ Financials" },
          { to: "/dashboard/documents",  label: "⊞ Documents" },
        ].map(item => (
          <Link key={item.to} to={item.to} style={{ textDecoration: "none" }}>
            <div style={{
              padding: "6px 14px", borderRadius: 20, fontSize: 12, border: `0.5px solid ${T.border2}`,
              background: "transparent", color: T.textSub, cursor: "pointer", transition: "all 0.15s",
            }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = T.green; e.currentTarget.style.color = T.green; }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = T.border2; e.currentTarget.style.color = T.textSub; }}>
              {item.label}
            </div>
          </Link>
        ))}
      </div>

      {/* Main grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginBottom: 16 }}>

        {/* Credit Score card */}
        <div style={{ background: T.surface, border: `0.5px solid ${T.border}`, borderRadius: 12, padding: '1.25rem', textAlign: 'center', gridRow: 'span 2' }}>
          <div style={{ fontSize: 10, color: T.muted, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '1rem' }}>Credit score</div>
          <div style={{ fontSize: 64, fontWeight: 500, color: gradeColor, lineHeight: 1 }}>{score.score}</div>
          <div style={{ fontSize: 13, color: gradeColor, marginTop: 8, marginBottom: '1.5rem' }}>{score.grade} Grade</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {subScores.map(s => (
              <div key={s.label}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: T.muted, marginBottom: 4 }}>
                  <span>{s.label}</span><span>{s.value}/100</span>
                </div>
                <div style={{ height: 3, background: T.border, borderRadius: 2 }}>
                  <div style={{ height: '100%', width: `${s.value}%`, background: s.value >= 80 ? T.green : s.value >= 60 ? T.yellow : T.red, borderRadius: 2 }} />
                </div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: '1.5rem', textAlign: 'left' }}>
            {score.positive_factors?.map((f: string) => (
              <div key={f} style={{ fontSize: 11, color: T.green, marginBottom: 6, display: 'flex', gap: 6 }}>
                <span>✓</span><span>{f}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Bank Summary */}
        <div style={{ background: T.surface, border: `0.5px solid ${T.border}`, borderRadius: 12, padding: '1.25rem', gridColumn: 'span 2' }}>
          <div style={{ fontSize: 10, color: T.muted, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '1rem' }}>Bank summary · HDFC XXXX4521</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 10 }}>
            {[
              ['Avg monthly credits', '₹40.3L', T.green],
              ['Avg monthly balance', '₹12L', T.text],
              ['Bounce count', '0', T.green],
              ['Recommended limit', `₹${(score.recommended_limit / 100000).toFixed(0)}L`, T.text],
            ].map(([label, val, color]) => (
              <div key={label as string} style={{ background: T.bg, borderRadius: 8, padding: '0.75rem' }}>
                <div style={{ fontSize: 10, color: T.muted, marginBottom: 6 }}>{label}</div>
                <div style={{ fontSize: 18, fontWeight: 500, color: color as string }}>{val}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Cash Flow Chart */}
        <div style={{ background: T.surface, border: `0.5px solid ${T.border}`, borderRadius: 12, padding: '1.25rem', gridColumn: 'span 2' }}>
          <div style={{ fontSize: 10, color: T.muted, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '1rem' }}>Cash flow (12 months · ₹L)</div>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={cashFlowData} barGap={2}>
              <XAxis dataKey="month" tick={{ fontSize: 10, fill: T.muted }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: T.muted }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: '#111', border: `0.5px solid ${T.border2}`, borderRadius: 6, fontSize: 12 }} />
              <Bar dataKey="credits" fill={T.green} radius={[2, 2, 0, 0]} name="Credits" />
              <Bar dataKey="debits" fill={T.red} opacity={0.4} radius={[2, 2, 0, 0]} name="Debits" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Loan Offers */}
      <div style={{ fontSize: 10, color: T.muted, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 12 }}>Loan offers</div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
        {loanOffers.map(offer => (
          <div key={offer.lender} style={{ background: T.surface, border: `0.5px solid ${offer.featured ? T.green : T.border}`, borderRadius: 12, padding: '1.25rem' }}>
            {offer.featured && (
              <div style={{ fontSize: 10, color: T.green, background: T.greenBg, padding: '3px 10px', borderRadius: 20, display: 'inline-block', marginBottom: 8 }}>Best match</div>
            )}
            <div style={{ fontSize: 14, fontWeight: 500, color: T.text, marginBottom: 4 }}>{offer.lender}</div>
            <div style={{ fontSize: 28, fontWeight: 500, color: T.text, margin: '0.5rem 0 0.25rem' }}>₹{(offer.amount / 100000).toFixed(0)}L</div>
            <div style={{ fontSize: 12, color: T.muted }}>{offer.rate}% per annum</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: T.muted, marginTop: '1rem', paddingTop: '1rem', borderTop: `0.5px solid ${T.border}` }}>
              <span>{offer.tenure ? `${offer.tenure}m` : 'Revolving'}</span>
              <span>Processing 1%</span>
            </div>
            <button
              onClick={() => offer.featured ? handleAccept(offer) : null}
              disabled={accepting === offer.lender || accepted === offer.lender}
              style={{
                marginTop: '0.75rem', width: '100%', padding: '10px',
                background: accepted === offer.lender ? T.green : offer.featured ? T.text : 'transparent',
                color: accepted === offer.lender ? '#fff' : offer.featured ? T.bg : T.text,
                border: `0.5px solid ${accepted === offer.lender ? T.green : offer.featured ? T.text : T.border2}`,
                borderRadius: 8, fontSize: 13, fontWeight: 500,
                cursor: offer.featured && !accepted ? 'pointer' : 'default',
                opacity: accepting === offer.lender ? 0.7 : 1,
              }}>
              {accepted === offer.lender ? '✓ Accepted' : accepting === offer.lender ? 'Processing...' : offer.featured ? 'Accept offer' : 'View details'}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}