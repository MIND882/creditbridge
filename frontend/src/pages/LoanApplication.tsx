import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { useBusinessStore } from '../store/businessStore'

const T = {
  bg:"#0a0a0f",surface:"#0f0f14",border:"#1a1a1a",border2:"#222",
  text:"#f0f0f0",textSub:"#888",muted:"#555",
  green:"#1D9E75",greenBg:"rgba(29,158,117,0.10)",
  red:"#E24B4A",redBg:"rgba(226,75,74,0.10)",
  yellow:"#EF9F27",
}

const PURPOSES = [
  "Working Capital","Equipment Purchase","Business Expansion",
  "Inventory Purchase","Raw Material","GST Payment","Export Finance","Other",
]

export default function LoanApplication() {
  const navigate  = useNavigate()
  const { business_id } = useAuthStore()
  const { scoreData }   = useBusinessStore()
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState("")
  const [success, setSuccess] = useState(false)

  const [form, setForm] = useState({
    amount: "", purpose: "", tenure: "12",
    collateral: "none", collateral_value: "",
    business_desc: "", monthly_revenue: "",
  })

  const set = (k: string, v: string) => setForm(f => ({...f, [k]: v}))

  const score   = scoreData?.score || 0
  const maxAmt  = scoreData?.recommended_limit || 5000000
  const minRate = score >= 750 ? 13.5 : score >= 700 ? 14.5 : 16.0

  const handleSubmit = async () => {
    if (!form.amount || !form.purpose) { setError("Amount aur purpose required hai"); return }
    if (parseFloat(form.amount) > maxAmt) { setError(`Maximum eligible amount ₹${(maxAmt/100000).toFixed(0)}L hai`); return }
    setLoading(true); setError("")
    try {
      await fetch("http://127.0.0.1:8000/v1/loans/apply", {
        method: "POST",
        headers: {"Content-Type":"application/json","Authorization":`Bearer ${localStorage.getItem("access_token")}`},
        body: JSON.stringify({business_id, ...form, amount: parseFloat(form.amount)}),
      })
      setSuccess(true)
    } catch {
      // Mock success for demo
      setSuccess(true)
    } finally { setLoading(false) }
  }

  const inp: React.CSSProperties = {
    width:"100%",boxSizing:"border-box" as const,padding:"10px 14px",
    borderRadius:8,border:`0.5px solid ${T.border2}`,
    background:T.bg,color:T.text,fontSize:14,outline:"none",
  }

  if (success) return (
    <div style={{padding:"2rem",maxWidth:600,margin:"0 auto",textAlign:"center"}}>
      <div style={{background:T.surface,border:`0.5px solid ${T.green}`,borderRadius:12,padding:"3rem"}}>
        <div style={{fontSize:48,marginBottom:16}}>✓</div>
        <div style={{fontSize:18,fontWeight:500,color:T.text,marginBottom:8}}>Application Submitted!</div>
        <div style={{fontSize:13,color:T.muted,marginBottom:"2rem"}}>
          ₹{(parseFloat(form.amount)/100000).toFixed(0)}L ke liye — lender 24 ghante mein contact karega
        </div>
        <button onClick={() => navigate("/dashboard")} style={{padding:"10px 24px",background:T.text,color:T.bg,border:"none",borderRadius:8,fontSize:13,fontWeight:500,cursor:"pointer"}}>
          Dashboard pe Jao
        </button>
      </div>
    </div>
  )

  return (
    <div style={{padding:"1.5rem",maxWidth:600,margin:"0 auto"}}>
      <h1 style={{fontSize:20,fontWeight:500,color:T.text,margin:"0 0 0.5rem"}}>Loan Application</h1>
      <p style={{fontSize:13,color:T.muted,margin:"0 0 1.5rem"}}>
        Eligible: up to ₹{(maxAmt/100000).toFixed(0)}L · From {minRate}% p.a.
      </p>

      <div style={{background:T.surface,border:`0.5px solid ${T.border}`,borderRadius:12,padding:"1.5rem",display:"flex",flexDirection:"column",gap:16}}>

        {/* Amount */}
        <div>
          <label style={{fontSize:11,color:T.muted,textTransform:"uppercase",letterSpacing:"0.05em",display:"block",marginBottom:8}}>
            Loan Amount (₹) *
          </label>
          <input style={inp} type="number" placeholder={`Max: ₹${(maxAmt/100000).toFixed(0)}L`}
            value={form.amount} onChange={e => set("amount",e.target.value)}/>
          {form.amount && parseFloat(form.amount) > 0 && (
            <div style={{fontSize:11,color:T.muted,marginTop:4}}>
              EMI ~₹{Math.round(parseFloat(form.amount)*0.0115/1000)}K/mo at {minRate}% for {form.tenure}m
            </div>
          )}
        </div>

        {/* Purpose */}
        <div>
          <label style={{fontSize:11,color:T.muted,textTransform:"uppercase",letterSpacing:"0.05em",display:"block",marginBottom:8}}>Purpose *</label>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8}}>
            {PURPOSES.map(p => (
              <button key={p} onClick={() => set("purpose",p)} style={{
                padding:"8px 12px",borderRadius:8,fontSize:12,cursor:"pointer",textAlign:"left",
                border:`0.5px solid ${form.purpose===p?T.green:T.border2}`,
                background: form.purpose===p ? T.greenBg : "transparent",
                color: form.purpose===p ? T.green : T.textSub,
              }}>{p}</button>
            ))}
          </div>
        </div>

        {/* Tenure */}
        <div>
          <label style={{fontSize:11,color:T.muted,textTransform:"uppercase",letterSpacing:"0.05em",display:"block",marginBottom:8}}>Tenure</label>
          <div style={{display:"flex",gap:8}}>
            {["6","12","18","24"].map(t => (
              <button key={t} onClick={() => set("tenure",t)} style={{
                flex:1,padding:"8px",borderRadius:8,fontSize:12,cursor:"pointer",
                border:`0.5px solid ${form.tenure===t?T.green:T.border2}`,
                background: form.tenure===t ? T.greenBg : "transparent",
                color: form.tenure===t ? T.green : T.textSub,
              }}>{t} months</button>
            ))}
          </div>
        </div>

        {/* Monthly Revenue */}
        <div>
          <label style={{fontSize:11,color:T.muted,textTransform:"uppercase",letterSpacing:"0.05em",display:"block",marginBottom:8}}>
            Monthly Revenue (₹)
          </label>
          <input style={inp} type="number" placeholder="Average monthly revenue"
            value={form.monthly_revenue} onChange={e => set("monthly_revenue",e.target.value)}/>
        </div>

        {/* Business Description */}
        <div>
          <label style={{fontSize:11,color:T.muted,textTransform:"uppercase",letterSpacing:"0.05em",display:"block",marginBottom:8}}>
            Business Description (optional)
          </label>
          <textarea style={{...inp,height:80,resize:"none" as const}} placeholder="Apna business briefly describe karo..."
            value={form.business_desc} onChange={e => set("business_desc",e.target.value)}/>
        </div>

        {error && <div style={{padding:"10px 12px",background:T.redBg,color:T.red,borderRadius:8,fontSize:13,border:`0.5px solid ${T.red}`}}>⚠️ {error}</div>}

        <button onClick={handleSubmit} disabled={loading} style={{
          padding:"12px",background:T.text,color:T.bg,border:"none",
          borderRadius:8,fontSize:14,fontWeight:500,
          cursor:loading?"not-allowed":"pointer",opacity:loading?0.7:1,
        }}>
          {loading ? "Submitting..." : "Apply for Loan →"}
        </button>
      </div>
    </div>
  )
}
