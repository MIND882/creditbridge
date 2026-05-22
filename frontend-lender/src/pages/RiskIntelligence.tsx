import { useState } from 'react'

const T = {
  bg:"#0a0a0f",surface:"#0f0f14",border:"#1a1a1a",border2:"#222",
  text:"#f0f0f0",textSub:"#888",muted:"#555",
  green:"#1D9E75",greenBg:"rgba(29,158,117,0.10)",
  red:"#E24B4A",redBg:"rgba(226,75,74,0.10)",
  yellow:"#EF9F27",yellowBg:"rgba(239,159,39,0.10)",
  blue:"#4A90E2",
}

// Mock data for demo
const MOCK_SECTOR = [
  {sector:"Textile",    count:42, avg_score:724, npa_rate:1.2},
  {sector:"Trading",    count:38, avg_score:698, npa_rate:2.1},
  {sector:"Manufacturing",count:27,avg_score:741, npa_rate:0.8},
  {sector:"Services",   count:19, avg_score:712, npa_rate:1.5},
  {sector:"Retail",     count:15, avg_score:685, npa_rate:2.8},
]

const MOCK_SCORE_DIST = [
  {range:"300-500",count:5, color:T.red},
  {range:"500-600",count:12,color:T.yellow},
  {range:"600-700",count:38,color:T.yellow},
  {range:"700-750",count:52,color:T.green},
  {range:"750-900",count:34,color:T.green},
]

const MOCK_ALERTS = [
  {business:"Sharma Textiles",  type:"Score Drop",    detail:"780→710 (last 30d)", severity:"amber"},
  {business:"Gupta Trading Co", type:"GST Gap",       detail:"3 months unfiled",   severity:"red"},
  {business:"Mehta Fabrics",    type:"Revenue Dip",   detail:"-40% last month",    severity:"amber"},
  {business:"Raj Exports",      type:"Bounce Risk",   detail:"2 consecutive months",severity:"red"},
]

const MOCK_VINTAGE = [
  {year:"<1yr",count:18},{year:"1-2yr",count:34},{year:"2-3yr",count:47},{year:"3-5yr",count:31},{year:"5+yr",count:11},
]

export default function RiskIntelligence() {
  const [activeTab, setActiveTab] = useState<"overview"|"sector"|"alerts">("overview")

  const totalBiz  = MOCK_SCORE_DIST.reduce((s,d) => s+d.count, 0)
  const avgScore  = 719
  const npaRate   = 1.6
  const greenPct  = Math.round((MOCK_SCORE_DIST.filter(d=>d.range.startsWith("7")).reduce((s,d)=>s+d.count,0)/totalBiz)*100)

  const tab = (name: typeof activeTab): React.CSSProperties => ({
    padding:"7px 18px",borderRadius:20,fontSize:12,cursor:"pointer",
    border:`0.5px solid ${activeTab===name?T.green:T.border2}`,
    background: activeTab===name ? T.greenBg : "transparent",
    color: activeTab===name ? T.green : T.textSub,
    fontWeight: activeTab===name ? 500 : 400,
  })

  return (
    <div style={{padding:"1.5rem",maxWidth:1100,margin:"0 auto"}}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:"1.5rem"}}>
        <h1 style={{fontSize:20,fontWeight:500,color:T.text,margin:0}}>Risk Intelligence</h1>
        <div style={{display:"flex",gap:8}}>
          <button style={tab("overview")}   onClick={() => setActiveTab("overview")}>Overview</button>
          <button style={tab("sector")}     onClick={() => setActiveTab("sector")}>Sector</button>
          <button style={tab("alerts")}     onClick={() => setActiveTab("alerts")}>
            Alerts <span style={{background:T.redBg,color:T.red,padding:"1px 6px",borderRadius:20,marginLeft:4,fontSize:10}}>{MOCK_ALERTS.length}</span>
          </button>
        </div>
      </div>

      {/* ── Overview ── */}
      {activeTab === "overview" && (
        <>
          {/* KPI Row */}
          <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:12,marginBottom:16}}>
            {[
              {label:"Total MSMEs",   value:totalBiz, unit:"",   color:T.text},
              {label:"Avg Score",     value:avgScore,  unit:"",  color:T.green},
              {label:"Green (700+)",  value:`${greenPct}%`,unit:"", color:T.green},
              {label:"Portfolio NPA", value:`${npaRate}%`,unit:"", color:npaRate<2?T.green:T.yellow},
            ].map(k => (
              <div key={k.label} style={{background:T.surface,border:`0.5px solid ${T.border}`,borderRadius:10,padding:"1rem 1.25rem"}}>
                <div style={{fontSize:10,color:T.muted,textTransform:"uppercase",letterSpacing:"0.07em",marginBottom:6}}>{k.label}</div>
                <div style={{fontSize:24,fontWeight:500,color:k.color}}>{k.value}</div>
              </div>
            ))}
          </div>

          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
            {/* Score Distribution */}
            <div style={{background:T.surface,border:`0.5px solid ${T.border}`,borderRadius:12,padding:"1.25rem"}}>
              <div style={{fontSize:10,color:T.muted,textTransform:"uppercase",letterSpacing:"0.07em",marginBottom:"1rem"}}>Score Distribution</div>
              <div style={{display:"flex",flexDirection:"column",gap:8}}>
                {MOCK_SCORE_DIST.map(row => (
                  <div key={row.range}>
                    <div style={{display:"flex",justifyContent:"space-between",fontSize:11,color:T.textSub,marginBottom:4}}>
                      <span>{row.range}</span>
                      <span>{row.count}</span>
                    </div>
                    <div style={{height:8,background:T.border2,borderRadius:999}}>
                      <div
                        style={{
                          height:"100%",
                          width:`${Math.round((row.count / totalBiz) * 100)}%`,
                          background:row.color,
                          borderRadius:999,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Vintage Distribution */}
            <div style={{background:T.surface,border:`0.5px solid ${T.border}`,borderRadius:12,padding:"1.25rem"}}>
              <div style={{fontSize:10,color:T.muted,textTransform:"uppercase",letterSpacing:"0.07em",marginBottom:"1rem"}}>Business Vintage</div>
              <div style={{display:"flex",flexDirection:"column",gap:8}}>
                {MOCK_VINTAGE.map(row => {
                  const pct = Math.round((row.count / totalBiz) * 100)
                  return (
                    <div key={row.year}>
                      <div style={{display:"flex",justifyContent:"space-between",fontSize:11,color:T.textSub,marginBottom:4}}>
                        <span>{row.year}</span>
                        <span>{row.count}</span>
                      </div>
                      <div style={{height:8,background:T.border2,borderRadius:999}}>
                        <div style={{height:"100%",width:`${pct}%`,background:T.blue,borderRadius:999}} />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        </>
      )}

      {/* ── Sector ── */}
      {activeTab === "sector" && (
        <div style={{background:T.surface,border:`0.5px solid ${T.border}`,borderRadius:12,overflow:"hidden"}}>
          <table style={{width:"100%",borderCollapse:"collapse"}}>
            <thead>
              <tr style={{background:"rgba(255,255,255,0.02)",borderBottom:`0.5px solid ${T.border}`}}>
                {["Sector","Count","Avg Score","NPA Rate","Risk Level"].map(h => (
                  <th key={h} style={{padding:"10px 16px",fontSize:10,fontWeight:500,color:T.muted,textTransform:"uppercase",letterSpacing:"0.06em",textAlign:"left"}}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {MOCK_SECTOR.map((s,i) => (
                <tr key={i} style={{borderBottom:i<MOCK_SECTOR.length-1?`0.5px solid ${T.border}`:"none"}}>
                  <td style={{padding:"12px 16px",fontSize:13,color:T.text,fontWeight:500}}>{s.sector}</td>
                  <td style={{padding:"12px 16px",fontSize:13,color:T.textSub}}>{s.count}</td>
                  <td style={{padding:"12px 16px",fontSize:13,color:s.avg_score>=720?T.green:T.yellow,fontWeight:500}}>{s.avg_score}</td>
                  <td style={{padding:"12px 16px",fontSize:13,color:s.npa_rate<2?T.green:T.red}}>{s.npa_rate}%</td>
                  <td style={{padding:"12px 16px"}}>
                    <span style={{
                      padding:"3px 10px",borderRadius:20,fontSize:11,fontWeight:500,
                      background: s.npa_rate<1.5?T.greenBg:s.npa_rate<2.5?T.yellowBg:T.redBg,
                      color: s.npa_rate<1.5?T.green:s.npa_rate<2.5?T.yellow:T.red,
                    }}>
                      {s.npa_rate<1.5?"LOW":s.npa_rate<2.5?"MEDIUM":"HIGH"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Alerts ── */}
      {activeTab === "alerts" && (
        <div style={{display:"flex",flexDirection:"column",gap:10}}>
          {MOCK_ALERTS.map((a,i) => (
            <div key={i} style={{
              background:T.surface,border:`0.5px solid ${a.severity==="red"?T.red:T.yellow}`,
              borderRadius:10,padding:"14px 16px",display:"flex",justifyContent:"space-between",alignItems:"center",
            }}>
              <div style={{display:"flex",alignItems:"center",gap:12}}>
                <span style={{fontSize:16}}>{a.severity==="red"?"🔴":"🟡"}</span>
                <div>
                  <div style={{fontSize:13,fontWeight:500,color:T.text}}>{a.business}</div>
                  <div style={{fontSize:11,color:T.textSub,marginTop:2}}>{a.type} — {a.detail}</div>
                </div>
              </div>
              <button style={{padding:"6px 14px",borderRadius:8,fontSize:12,cursor:"pointer",border:`0.5px solid ${T.border2}`,background:"transparent",color:T.textSub}}>
                View →
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
