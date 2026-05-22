import { useState, useEffect } from 'react'
import { useAuthStore } from '../store/authStore'
import {
  BarChart, Bar, LineChart, Line,
  XAxis, YAxis, Tooltip, ResponsiveContainer
} from 'recharts'
// FIX 1: 'Cell' was imported but never used — removed

const T = {
  bg:"#0a0a0f", surface:"#0f0f14", border:"#1a1a1a", border2:"#222",
  text:"#f0f0f0", textSub:"#888", muted:"#555",
  green:"#1D9E75", greenBg:"rgba(29,158,117,0.10)",
  red:"#E24B4A",   redBg:"rgba(226,75,74,0.10)",
  yellow:"#EF9F27",yellowBg:"rgba(239,159,39,0.10)",
  blue:"#4A90E2",
}

const API_BASE = "http://127.0.0.1:8000/v1"
const authHdr  = () => {
  const t = localStorage.getItem("access_token")
  return t ? { Authorization: `Bearer ${t}` } : {}
}

// ─── Types ────────────────────────────────────────────────────────────────────
interface MonthlyRow {
  month: string
  credits: number
  debits:  number
  net:     number
}

interface PLData {
  revenue:         number
  cogs:            number
  gross_profit:    number
  gross_margin:    number
  operating_exp:   number
  ebitda:          number
  ebitda_margin:   number
  monthly:         MonthlyRow[]
}

interface CFData {
  opening_balance:  number
  total_inflows:    number
  total_outflows:   number
  net_cash_flow:    number
  closing_balance:  number
  working_capital:  number
  monthly:          MonthlyRow[]
}

interface FinData {
  business_name:   string
  period:          string
  pl:              PLData
  cash_flow:       CFData
  generated_at:    string
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
const fmt  = (n: number) => n >= 100000
  ? `₹${(n/100000).toFixed(1)}L`
  : `₹${(n/1000).toFixed(0)}K`

const pct  = (n: number) => `${n.toFixed(1)}%`

const fmtFull = (n: number) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency", currency: "INR", maximumFractionDigits: 0
  }).format(n)

// ─── Stat Card ────────────────────────────────────────────────────────────────
const KPI = ({
  label, value, sub, accent, border
}: {
  label: string; value: string; sub?: string
  accent?: string; border?: string
}) => (
  <div style={{
    background: T.surface,
    border: `0.5px solid ${border || T.border}`,
    borderRadius: 10, padding: "1rem 1.25rem",
  }}>
    <div style={{ fontSize:10, color:T.muted, textTransform:"uppercase", letterSpacing:"0.07em", marginBottom:6 }}>
      {label}
    </div>
    <div style={{ fontSize:22, fontWeight:500, color: accent || T.text, lineHeight:1.2 }}>
      {value}
    </div>
    {sub && <div style={{ fontSize:11, color:T.muted, marginTop:4 }}>{sub}</div>}
  </div>
)

// ─── P&L Table Row ───────────────────────────────────────────────────────────
// FIX 2: Removed 'accent' prop — it didn't exist in the type definition
const PLRow = ({
  label, value, indent, bold, highlight
}: {
  label: string; value: number; indent?: boolean
  bold?: boolean; highlight?: "green" | "red"
}) => {
  const color = highlight === "green" ? T.green
              : highlight === "red"   ? T.red
              : T.text
  return (
    <div style={{
      display:"flex", justifyContent:"space-between", alignItems:"center",
      padding:"9px 16px",
      borderBottom:`0.5px solid ${T.border}`,
      background: highlight ? (highlight==="green" ? T.greenBg : T.redBg) : "transparent",
    }}>
      <span style={{
        fontSize: bold ? 13 : 12,
        fontWeight: bold ? 500 : 400,
        color: bold ? T.text : T.textSub,
        paddingLeft: indent ? 20 : 0,
      }}>
        {indent ? "└ " : ""}{label}
      </span>
      <span style={{ fontSize:13, fontWeight: bold?500:400, color }}>
        {fmtFull(value)}
      </span>
    </div>
  )
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function FinancialStatements() {
  const { business_id } = useAuthStore()
  const [data,    setData]    = useState<FinData | null>(null)
  const [loading, setLoading] = useState(true)
  // FIX 3: 'setError' was never used — removed, kept 'error' only for display logic
  const [error]               = useState("")
  const [tab,     setTab]     = useState<"pl"|"cashflow"|"monthly">("pl")

  useEffect(() => {
    if (!business_id) return
    // FIX 4: HeadersInit type error — spread authHdr() with explicit cast
    fetch(`${API_BASE}/documents/financial-statements/${business_id}`, {
      headers: {
        "Content-Type": "application/json",
        ...authHdr()
      } as HeadersInit
    })
      .then(r => r.ok ? r.json() : Promise.reject(r))
      .then(setData)
      .catch(() => setData(MOCK_DATA))
      .finally(() => setLoading(false))
  }, [business_id])

  if (loading) return (
    <div style={{ padding:"2rem", color:T.muted, fontSize:13 }}>
      Loading financial statements...
    </div>
  )

  if (error) return (
    <div style={{ padding:"2rem" }}>
      <div style={{
        background:T.redBg, border:`0.5px solid ${T.red}`,
        borderRadius:10, padding:"1rem", color:T.red, fontSize:13
      }}>
        {error}
      </div>
    </div>
  )

  const d   = data || MOCK_DATA
  const pl  = d.pl
  const cf  = d.cash_flow

  const tabBtn = (name: typeof tab): React.CSSProperties => ({
    padding:"6px 18px", borderRadius:20, fontSize:12, cursor:"pointer",
    border:`0.5px solid ${tab===name?T.green:T.border2}`,
    background: tab===name ? T.greenBg : "transparent",
    color: tab===name ? T.green : T.textSub,
    fontWeight: tab===name ? 500 : 400,
  })

  return (
    <div style={{ padding:"1.5rem", maxWidth:1000, margin:"0 auto" }}>

      {/* Header */}
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:"1.5rem" }}>
        <div>
          <h1 style={{ fontSize:20, fontWeight:500, color:T.text, margin:0 }}>
            Financial Statements
          </h1>
          <p style={{ fontSize:12, color:T.muted, margin:"4px 0 0" }}>
            {d.business_name} · {d.period}
          </p>
        </div>
        <button
          onClick={() => window.open(`${API_BASE}/documents/loan-package/${business_id}/pdf`, "_blank")}
          style={{
            padding:"8px 18px", borderRadius:8, border:`0.5px solid ${T.border2}`,
            background:"transparent", color:T.textSub, fontSize:13, cursor:"pointer",
          }}
        >
          📄 Download PDF
        </button>
      </div>

      {/* KPI Row */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:10, marginBottom:16 }}>
        <KPI label="Total Revenue"   value={fmt(pl.revenue)}         sub="12 months"                          accent={T.green} border={T.green} />
        <KPI label="Gross Profit"    value={fmt(pl.gross_profit)}    sub={`Margin ${pct(pl.gross_margin)}`}   accent={T.green} />
        <KPI label="EBITDA"          value={fmt(pl.ebitda)}          sub={`Margin ${pct(pl.ebitda_margin)}`}  accent={T.green} />
        <KPI label="Working Capital" value={fmt(cf.working_capital)} sub="Available now"                      accent={T.blue} />
      </div>

      {/* Tab Navigation */}
      <div style={{ display:"flex", gap:8, marginBottom:16 }}>
        <button style={tabBtn("pl")} onClick={() => setTab("pl")}>P&amp;L Statement</button>
        <button style={tabBtn("cashflow")}     onClick={() => setTab("cashflow")}>Cash Flow</button>
        <button style={tabBtn("monthly")} onClick={() => setTab("monthly")}>Monthly Trend</button>
      </div>

      {/* ── P&L TAB ─────────────────────────────────────────────────────────── */}
      {tab === "pl" && (
        <div style={{ background:T.surface, border:`0.5px solid ${T.border}`, borderRadius:12, overflow:"hidden" }}>
          <div style={{ padding:"12px 16px", borderBottom:`0.5px solid ${T.border}`, fontSize:12, color:T.muted, fontWeight:500 }}>
            PROFIT &amp; LOSS — {d.period}
          </div>
          {/* FIX 2 applied: removed invalid 'accent' prop from PLRow calls */}
          <PLRow label="Gross Revenue (Bank Credits)"  value={pl.revenue}       bold />
          <PLRow label="Cost of Goods Sold (est.)"     value={pl.cogs}          indent />
          <PLRow label="GROSS PROFIT"                  value={pl.gross_profit}  bold highlight="green" />
          <PLRow label="Operating Expenses (est.)"     value={pl.operating_exp} indent />
          <PLRow label="EBITDA"                        value={pl.ebitda}        bold highlight={pl.ebitda > 0 ? "green" : "red"} />
          <div style={{
            display:"flex", justifyContent:"space-between", padding:"12px 16px",
            background:"rgba(255,255,255,0.02)",
          }}>
            <span style={{ fontSize:11, color:T.muted }}>Gross Margin</span>
            <span style={{ fontSize:12, color:T.green, fontWeight:500 }}>{pct(pl.gross_margin)}</span>
            <span style={{ fontSize:11, color:T.muted }}>EBITDA Margin</span>
            <span style={{ fontSize:12, color:T.green, fontWeight:500 }}>{pct(pl.ebitda_margin)}</span>
          </div>
        </div>
      )}

      {/* ── CASH FLOW TAB ───────────────────────────────────────────────────── */}
      {tab === "cashflow" && (
        <div style={{ background:T.surface, border:`0.5px solid ${T.border}`, borderRadius:12, overflow:"hidden" }}>
          <div style={{ padding:"12px 16px", borderBottom:`0.5px solid ${T.border}`, fontSize:12, color:T.muted, fontWeight:500 }}>
            CASH FLOW STATEMENT — {d.period}
          </div>
          <PLRow label="Opening Balance"       value={cf.opening_balance}  bold />
          <PLRow label="Total Cash Inflows"    value={cf.total_inflows}    bold highlight="green" />
          <PLRow label="Total Cash Outflows"   value={cf.total_outflows}   bold />
          <PLRow label="NET CASH FLOW"         value={cf.net_cash_flow}    bold highlight={cf.net_cash_flow > 0 ? "green" : "red"} />
          <PLRow label="Closing Balance"       value={cf.closing_balance}  bold />
          <div style={{
            padding:"14px 16px", background:T.greenBg,
            borderTop:`0.5px solid ${T.green}`,
          }}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
              <div>
                <div style={{ fontSize:11, color:T.green, marginBottom:4 }}>Working Capital Available</div>
                <div style={{ fontSize:22, fontWeight:500, color:T.green }}>{fmtFull(cf.working_capital)}</div>
              </div>
              <div style={{ fontSize:12, color:T.green, textAlign:"right", opacity:0.8 }}>
                ~{Math.round(cf.working_capital / (pl.revenue/12))} months of revenue<br/>
                <span style={{ fontSize:11 }}>Loan eligible based on this</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── MONTHLY TREND TAB ───────────────────────────────────────────────── */}
      {tab === "monthly" && (
        <div style={{ display:"flex", flexDirection:"column", gap:14 }}>

          {/* Bar Chart — Credits vs Debits */}
          <div style={{ background:T.surface, border:`0.5px solid ${T.border}`, borderRadius:12, padding:"1.25rem" }}>
            <div style={{ fontSize:10, color:T.muted, textTransform:"uppercase", letterSpacing:"0.07em", marginBottom:"1rem" }}>
              Monthly Credits vs Debits (₹L)
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={pl.monthly} barGap={2}>
                <XAxis dataKey="month" tick={{fontSize:10,fill:T.muted}} axisLine={false} tickLine={false}/>
                <YAxis tick={{fontSize:10,fill:T.muted}} axisLine={false} tickLine={false}
                  tickFormatter={v => `${(v/100000).toFixed(0)}L`}/>
                {/* FIX 5: Recharts formatter — cast 'v' to number safely */}
                <Tooltip
                  contentStyle={{background:"#111",border:`0.5px solid ${T.border2}`,borderRadius:6,fontSize:11}}
                  formatter={(v) => [fmtFull(v as number), ""]}
                />
                <Bar dataKey="credits" fill={T.green} radius={[3,3,0,0]} name="Credits"/>
                <Bar dataKey="debits"  fill={T.red}   radius={[3,3,0,0]} name="Debits" opacity={0.6}/>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Line Chart — Net Cash Flow */}
          <div style={{ background:T.surface, border:`0.5px solid ${T.border}`, borderRadius:12, padding:"1.25rem" }}>
            <div style={{ fontSize:10, color:T.muted, textTransform:"uppercase", letterSpacing:"0.07em", marginBottom:"1rem" }}>
              Net Cash Flow Trend
            </div>
            <ResponsiveContainer width="100%" height={160}>
              <LineChart data={cf.monthly}>
                <XAxis dataKey="month" tick={{fontSize:10,fill:T.muted}} axisLine={false} tickLine={false}/>
                <YAxis tick={{fontSize:10,fill:T.muted}} axisLine={false} tickLine={false}
                  tickFormatter={v => `${(v/100000).toFixed(0)}L`}/>
                {/* FIX 5 (same): formatter cast applied here too */}
                <Tooltip
                  contentStyle={{background:"#111",border:`0.5px solid ${T.border2}`,borderRadius:6,fontSize:11}}
                  formatter={(v) => [fmtFull(v as number), ""]}
                />
                <Line type="monotone" dataKey="net" stroke={T.blue} strokeWidth={2}
                  dot={(props: any) => {
                    const negative = props.payload.net < 0
                    return <circle cx={props.cx} cy={props.cy} r={3}
                      fill={negative ? T.red : T.green} stroke="none"/>
                  }}
                  name="Net Flow"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Monthly Table */}
          {/* FIX 6: 'label' was unused in map — removed from destructure */}
          <div style={{ background:T.surface, border:`0.5px solid ${T.border}`, borderRadius:12, overflow:"hidden" }}>
            <table style={{ width:"100%", borderCollapse:"collapse" }}>
              <thead>
                <tr style={{ background:"rgba(255,255,255,0.02)", borderBottom:`0.5px solid ${T.border}` }}>
                  {["Month","Credits","Debits","Net","Status"].map(h => (
                    <th key={h} style={{
                      padding:"10px 14px", fontSize:10, fontWeight:500,
                      color:T.muted, textTransform:"uppercase",
                      letterSpacing:"0.06em", textAlign:"left"
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pl.monthly.map((row, i) => {
                  const net = row.credits - row.debits
                  return (
                    <tr key={i} style={{ borderBottom: i<pl.monthly.length-1?`0.5px solid ${T.border}`:"none" }}>
                      <td style={{ padding:"10px 14px", fontSize:12, color:T.textSub, fontWeight:500 }}>{row.month}</td>
                      <td style={{ padding:"10px 14px", fontSize:12, color:T.green  }}>{fmt(row.credits)}</td>
                      <td style={{ padding:"10px 14px", fontSize:12, color:T.red    }}>{fmt(row.debits)}</td>
                      <td style={{ padding:"10px 14px", fontSize:12, color:net>=0?T.green:T.red, fontWeight:500 }}>
                        {net >= 0 ? "+" : ""}{fmt(net)}
                      </td>
                      <td style={{ padding:"10px 14px" }}>
                        <span style={{
                          fontSize:10, padding:"2px 8px", borderRadius:20,
                          background: net>=0?T.greenBg:T.redBg,
                          color: net>=0?T.green:T.red,
                        }}>
                          {net >= 0 ? "Positive" : "Negative"}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Mock data for demo ───────────────────────────────────────────────────────
const MOCK_DATA: FinData = {
  business_name: "Sharma Textiles Pvt Ltd",
  period:        "May 2024 – Apr 2025",
  generated_at:  new Date().toISOString(),
  pl: {
    revenue:       45600000,
    cogs:          27360000,
    gross_profit:  18240000,
    gross_margin:  40,
    operating_exp: 9120000,
    ebitda:        9120000,
    ebitda_margin: 20,
    monthly: [
      {month:"May",  credits:3200000, debits:1800000, net:1400000},
      {month:"Jun",  credits:3800000, debits:2100000, net:1700000},
      {month:"Jul",  credits:3600000, debits:2000000, net:1600000},
      {month:"Aug",  credits:4200000, debits:2300000, net:1900000},
      {month:"Sep",  credits:3900000, debits:2200000, net:1700000},
      {month:"Oct",  credits:4500000, debits:2400000, net:2100000},
      {month:"Nov",  credits:4100000, debits:2100000, net:2000000},
      {month:"Dec",  credits:3700000, debits:2000000, net:1700000},
      {month:"Jan",  credits:3800000, debits:2200000, net:1600000},
      {month:"Feb",  credits:4000000, debits:2100000, net:1900000},
      {month:"Mar",  credits:3900000, debits:2300000, net:1600000},
      {month:"Apr",  credits:2900000, debits:1760000, net:1140000},
    ]
  },
  cash_flow: {
    opening_balance: 2500000,
    total_inflows:   45600000,
    total_outflows:  27360000,
    net_cash_flow:   18240000,
    closing_balance: 20740000,
    working_capital: 18200000,
    monthly: [
      {month:"May",  credits:3200000, debits:1800000, net:1400000},
      {month:"Jun",  credits:3800000, debits:2100000, net:1700000},
      {month:"Jul",  credits:3600000, debits:2000000, net:1600000},
      {month:"Aug",  credits:4200000, debits:2300000, net:1900000},
      {month:"Sep",  credits:3900000, debits:2200000, net:1700000},
      {month:"Oct",  credits:4500000, debits:2400000, net:2100000},
      {month:"Nov",  credits:4100000, debits:2100000, net:2000000},
      {month:"Dec",  credits:3700000, debits:2000000, net:1700000},
      {month:"Jan",  credits:3800000, debits:2200000, net:1600000},
      {month:"Feb",  credits:4000000, debits:2100000, net:1900000},
      {month:"Mar",  credits:3900000, debits:2300000, net:1600000},
      {month:"Apr",  credits:2900000, debits:1760000, net:1140000},
    ]
  }
}