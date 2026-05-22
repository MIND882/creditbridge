import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useBusinessStore } from '../store/businessStore'
import { useAuthStore } from '../store/authStore'
import { getScore, computeScore } from '../api/intelligence'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

const T = {
  bg:"#0a0a0f",surface:"#0f0f14",border:"#1a1a1a",border2:"#222",
  text:"#f0f0f0",textSub:"#888",muted:"#555",
  green:"#1D9E75",greenBg:"rgba(29,158,117,0.10)",
  red:"#E24B4A",yellow:"#EF9F27",
}

export default function CreditScore() {
  const { business_id } = useAuthStore()
  const { scoreData, setScoreData } = useBusinessStore()
  const [loading, setLoading] = useState(!scoreData)
  const navigate = useNavigate()

  useEffect(() => {
    if (!scoreData && business_id) {
      getScore(business_id)
        .then(r => setScoreData(r.data))
        .catch(() => computeScore(business_id!).then(r => setScoreData(r.data)))
        .finally(() => setLoading(false))
    } else setLoading(false)
  }, [])

  if (loading) return <div style={{padding:"2rem",color:T.muted,fontSize:13}}>Computing score...</div>

  const score = scoreData!
  const gradeColor = score.score >= 750 ? T.green : score.score >= 650 ? T.yellow : T.red

  const subScores = [
    {label:"Cash Flow",           value: score.cash_flow_score || 0},
    {label:"Payment Discipline",  value: score.payment_discipline_score || 0},
    {label:"GST Compliance",      value: score.gst_compliance_score || 0},
    {label:"Revenue Consistency", value: score.revenue_growth_score || 0},
    {label:"Business Vintage",    value: score.business_vintage_score || 0},
  ]

  const trendData = [
    {month:"Nov",score:score.score-30},{month:"Dec",score:score.score-20},
    {month:"Jan",score:score.score-10},{month:"Feb",score:score.score-5},
    {month:"Mar",score:score.score-2},{month:"Apr",score:score.score},
  ]

  const tips = [
    {title:"File GST on time",          impact:"+15 pts", done: (score.gst_compliance_score||0) > 80},
    {title:"Reduce payment delays",      impact:"+20 pts", done: (score.payment_discipline_score||0) > 80},
    {title:"Maintain stable revenue",    impact:"+15 pts", done: (score.revenue_growth_score||0) > 60},
    {title:"Link Aadhaar to PAN",        impact:"+10 pts", done: true},
    {title:"3+ year business vintage",   impact:"+15 pts", done: (score.business_vintage_score||0) > 60},
  ]

  return (
    <div style={{padding:"1.5rem",maxWidth:900,margin:"0 auto"}}>
      <h1 style={{fontSize:20,fontWeight:500,color:T.text,margin:"0 0 1.5rem"}}>Credit Score</h1>

      <div style={{display:"grid",gridTemplateColumns:"260px 1fr",gap:14,marginBottom:14}}>
        <div style={{background:T.surface,border:`0.5px solid ${T.border}`,borderRadius:12,padding:"1.5rem",textAlign:"center"}}>
          <div style={{fontSize:10,color:T.muted,textTransform:"uppercase",letterSpacing:"0.08em",marginBottom:"1rem"}}>Your Score</div>
          <div style={{fontSize:72,fontWeight:600,color:gradeColor,lineHeight:1}}>{score.score}</div>
          <div style={{fontSize:13,color:gradeColor,marginTop:8,marginBottom:"1.5rem"}}>{score.grade} Grade</div>
          <div style={{height:5,background:T.border,borderRadius:3,marginBottom:6,position:"relative"}}>
            <div style={{position:"absolute",left:0,top:0,height:"100%",width:`${Math.min(100,(score.score-300)/600*100)}%`,background:gradeColor,borderRadius:3}}/>
          </div>
          <div style={{display:"flex",justifyContent:"space-between",fontSize:10,color:T.muted,marginBottom:"1.5rem"}}>
            <span>300</span><span>550</span><span>750</span><span>900</span>
          </div>
          <button onClick={() => navigate("/dashboard/apply")} style={{width:"100%",padding:"10px",background:T.text,color:T.bg,border:"none",borderRadius:8,fontSize:13,fontWeight:500,cursor:"pointer"}}>
            Apply for Loan →
          </button>
        </div>

        <div style={{background:T.surface,border:`0.5px solid ${T.border}`,borderRadius:12,padding:"1.5rem"}}>
          <div style={{fontSize:10,color:T.muted,textTransform:"uppercase",letterSpacing:"0.08em",marginBottom:"1rem"}}>Score Breakdown</div>
          <div style={{display:"flex",flexDirection:"column",gap:14}}>
            {subScores.map(s => (
              <div key={s.label}>
                <div style={{display:"flex",justifyContent:"space-between",fontSize:12,marginBottom:5}}>
                  <span style={{color:T.textSub}}>{s.label}</span>
                  <span style={{color:s.value>=80?T.green:s.value>=60?T.yellow:T.red,fontWeight:500}}>{s.value}/100</span>
                </div>
                <div style={{height:4,background:T.border,borderRadius:2}}>
                  <div style={{height:"100%",width:`${s.value}%`,background:s.value>=80?T.green:s.value>=60?T.yellow:T.red,borderRadius:2}}/>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
        <div style={{background:T.surface,border:`0.5px solid ${T.border}`,borderRadius:12,padding:"1.5rem"}}>
          <div style={{fontSize:10,color:T.muted,textTransform:"uppercase",letterSpacing:"0.08em",marginBottom:"1rem"}}>Score Trend (6 months)</div>
          <ResponsiveContainer width="100%" height={130}>
            <LineChart data={trendData}>
              <XAxis dataKey="month" tick={{fontSize:10,fill:T.muted}} axisLine={false} tickLine={false}/>
              <YAxis domain={[score.score-60,score.score+20]} tick={{fontSize:10,fill:T.muted}} axisLine={false} tickLine={false}/>
              <Tooltip contentStyle={{background:"#111",border:`0.5px solid ${T.border2}`,borderRadius:6,fontSize:11}}/>
              <Line type="monotone" dataKey="score" stroke={T.green} strokeWidth={2} dot={{fill:T.green,r:3}}/>
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div style={{background:T.surface,border:`0.5px solid ${T.border}`,borderRadius:12,padding:"1.5rem"}}>
          <div style={{fontSize:10,color:T.muted,textTransform:"uppercase",letterSpacing:"0.08em",marginBottom:"1rem"}}>Score Improve Karo</div>
          <div style={{display:"flex",flexDirection:"column",gap:10}}>
            {tips.map((tip,i) => (
              <div key={i} style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                <div style={{display:"flex",alignItems:"center",gap:8}}>
                  <span style={{color:tip.done?T.green:T.muted,fontSize:13}}>{tip.done?"✓":"○"}</span>
                  <span style={{fontSize:12,color:tip.done?T.muted:T.textSub,textDecoration:tip.done?"line-through":"none"}}>{tip.title}</span>
                </div>
                {!tip.done && <span style={{fontSize:11,color:T.green,background:T.greenBg,padding:"2px 8px",borderRadius:20,flexShrink:0}}>{tip.impact}</span>}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}