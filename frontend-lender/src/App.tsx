import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import Login from './pages/Login'
import Pool from './pages/Pool'
import BusinessDetail from './pages/BusinessDetail'
import Portfolio from './pages/Portfolio'
import Alerts from './pages/Alerts'
import RiskIntelligence from './pages/RiskIntelligence'
import { getApiKey, removeApiKey } from './api/client'

// ─── Theme ────────────────────────────────────────────────────────────────────
const T = {
  bg:       "#0a0a0f",
  surface:  "#0f0f14",
  surface2: "#13131a",
  border:   "#1a1a24",
  border2:  "#222230",
  text:     "#f0f0f0",
  textSub:  "#888",
  muted:    "#444",
  green:    "#1D9E75",
  greenBg:  "rgba(29,158,117,0.10)",
  red:      "#E24B4A",
  redBg:    "rgba(226,75,74,0.08)",
  yellow:   "#EF9F27",
  blue:     "#4A90E2",
  blueBg:   "rgba(74,144,226,0.08)",
  purple:   "#8B5CF6",
}

// ─── Nav items ────────────────────────────────────────────────────────────────
const NAV = [
  { path: "/pool",            icon: "◈", label: "MSME Pool" },
  { path: "/portfolio",       icon: "◎", label: "Portfolio" },
  { path: "/alerts",          icon: "◉", label: "Alerts" },
  { path: "/risk-intelligence", icon: "◇", label: "Risk Intel" },
]

// ─── Auth Guard ───────────────────────────────────────────────────────────────
function Guard({ children }: { children: React.ReactNode }) {
  return getApiKey() ? <>{children}</> : <Navigate to="/" />
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────
function Sidebar() {
  const location = useLocation()
  const navigate = useNavigate()
  const [collapsed, setCollapsed] = useState(false)

  const handleSignOut = () => {
    removeApiKey()
    navigate('/')
  }

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
    }}>
      {/* Logo */}
      <div style={{
        padding: collapsed ? "1.25rem 0" : "1.25rem 1rem",
        borderBottom: `0.5px solid ${T.border}`,
        display: "flex",
        alignItems: "center",
        justifyContent: collapsed ? "center" : "space-between",
        gap: 8,
      }}>
        {!collapsed && (
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: T.green, letterSpacing: "0.05em" }}>
              CREDITBRIDGE
            </div>
            <div style={{ fontSize: 9, color: T.muted, letterSpacing: "0.1em", marginTop: 1 }}>
              LENDER PORTAL
            </div>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          style={{
            background: "none", border: "none", cursor: "pointer",
            color: T.muted, fontSize: 14, padding: 4,
            display: "flex", alignItems: "center",
          }}
        >
          {collapsed ? "→" : "←"}
        </button>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: "0.75rem 0" }}>
        {NAV.map(item => {
          const active = location.pathname === item.path ||
            (item.path === '/pool' && location.pathname.startsWith('/business'))
          return (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              style={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: collapsed ? "10px 0" : "10px 16px",
                justifyContent: collapsed ? "center" : "flex-start",
                background: active ? T.greenBg : "transparent",
                border: "none",
                borderLeft: `2px solid ${active ? T.green : "transparent"}`,
                cursor: "pointer",
                color: active ? T.green : T.textSub,
                fontSize: 12,
                fontWeight: active ? 500 : 400,
                transition: "all 0.15s",
              }}
            >
              <span style={{ fontSize: 14, lineHeight: 1 }}>{item.icon}</span>
              {!collapsed && <span>{item.label}</span>}
            </button>
          )
        })}
      </nav>

      {/* Sign out */}
      <div style={{ padding: "0.75rem 0", borderTop: `0.5px solid ${T.border}` }}>
        <button
          onClick={handleSignOut}
          style={{
            width: "100%",
            display: "flex",
            alignItems: "center",
            gap: 10,
            padding: collapsed ? "10px 0" : "10px 16px",
            justifyContent: collapsed ? "center" : "flex-start",
            background: "none",
            border: "none",
            cursor: "pointer",
            color: T.muted,
            fontSize: 12,
          }}
        >
          <span style={{ fontSize: 14 }}>⊗</span>
          {!collapsed && <span>Sign out</span>}
        </button>
      </div>
    </div>
  )
}

// ─── Dashboard Layout ─────────────────────────────────────────────────────────
function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      display: "flex",
      minHeight: "100vh",
      background: T.bg,
      color: T.text,
      fontFamily: "'DM Mono', 'Fira Code', monospace",
    }}>
      <Sidebar />
      <main style={{ flex: 1, overflow: "auto" }}>
        {children}
      </main>
    </div>
  )
}

// ─── App ──────────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <BrowserRouter>
      <div style={{
        background: T.bg,
        minHeight: "100vh",
        color: T.text,
        fontFamily: "'DM Mono', 'Fira Code', monospace",
      }}>
        <Routes>
          {/* Public */}
          <Route path="/" element={<Login />} />

          {/* Protected — with sidebar layout */}
          <Route path="/pool" element={
            <Guard>
              <DashboardLayout><Pool /></DashboardLayout>
            </Guard>
          }/>
          <Route path="/business/:id" element={
            <Guard>
              <DashboardLayout><BusinessDetail /></DashboardLayout>
            </Guard>
          }/>
          <Route path="/portfolio" element={
            <Guard>
              <DashboardLayout><Portfolio /></DashboardLayout>
            </Guard>
          }/>
          <Route path="/alerts" element={
            <Guard>
              <DashboardLayout><Alerts /></DashboardLayout>
            </Guard>
          }/>
          <Route path="/risk-intelligence" element={
            <Guard>
              <DashboardLayout><RiskIntelligence /></DashboardLayout>
            </Guard>
          }/>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}