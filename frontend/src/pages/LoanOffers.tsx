import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useBusinessStore } from '../store/businessStore'
import { useAuthStore } from '../store/authStore'
import { acceptOffer } from '../api/intelligence'

const T = {
  bg:"#0a0a0f",surface:"#0f0f14",border:"#1a1a1a",border2:"#222",
  text:"#f0f0f0",textSub:"#888",muted:"#555",
  green:"#1D9E75",greenBg:"rgba(29,158,117,0.10)",
  red:"#E24B4A",redBg:"rgba(226,75,74,0.10)",
  yellow:"#EF9F27",yellowBg:"rgba(239,159,39,0.10)",
}

const OFFERS = [
  {lender:"Lendingkart NBFC",    amount:7500000, rate:13.5, tenure:12, fee:1.0, featured:true,  tag:"Best Rate"},
  {lender:"Kotak Mahindra Bank", amount:6000000, rate:14.2, tenure:24, fee:1.5, featured:false, tag:"Best Tenure"},
  {lender:"HDFC Overdraft",      amount:5000000, rate:15.0, tenure:0,  fee:1.0, featured:false, tag:"Revolving"},
  {lender:"Flexi Loans",         amount:3000000, rate:18.0, tenure:6,  fee:2.0, featured:false, tag:"Fast Approval"},
  {lender:"Axis Bank MSME",      amount:5500000, rate:14.8, tenure:18, fee:1.25,featured:false, tag:""},
]

export default function LoanOffers() {
  const navigate = useNavigate()
  const { business_id } = useAuthStore()
  const { scoreData } = useBusinessStore()
  const [accepting, setAccepting] = useState<string|null>(null)
  const [accepted,  setAccepted]  = useState<string|null>(null)
  const [error, setError] = useState("")

  const score = scoreData?.score || 0
  const eligible = OFFERS.filter(o => {
    if (score >= 720) return true
    if (score >= 700) return o.rate <= 15
    if (score >= 650) return o.rate <= 14 || o.lender === "Lendingkart NBFC" || o.lender === "Flexi Loans"
    return o.lender === "Flexi Loans"
  })

  const handleAccept = async (offer: typeof OFFERS[0]) => {
    setAccepting(offer.lender); setError("")
    try {
      await acceptOffer({business_id: business_id!, lender_name: offer.lender, amount: offer.amount, rate: offer.rate})
      setAccepted(offer.lender)
    } catch { setError("Something went wrong — try again") }
    finally { setAccepting(null) }
  }

  const fmt = (n: number) => `₹${(n/100000).toFixed(0)}L`
  const emi = (amount: number, rate: number, months: number) => {
    if (!months) return "Revolving"
    const r = rate / 100 / 12
    const e = amount * r * Math.pow(1+r, months) / (Math.pow(1+r, months) - 1)
    return `₹${Math.round(e/1000)}K/mo`
  }

  return (
    <div style={{padding:"1.5rem",maxWidth:1000,margin:"0 auto"}}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:"1.5rem"}}>
        <div>
          <h1 style={{fontSize:20,fontWeight:500,color:T.text,margin:0}}>Loan Offers</h1>
          <p style={{fontSize:13,color:T.muted,margin:"4px 0 0"}}>
            Score {score} ke basis pe — {eligible.length} offers available
          </p>
        </div>
        <button onClick={() => navigate("/dashboard/apply")} style={{padding:"8px 18px",background:T.text,color:T.bg,border:"none",borderRadius:8,fontSize:13,fontWeight:500,cursor:"pointer"}}>
          Custom Amount Apply →
        </button>
      </div>

      {error && <div style={{padding:"10px 14px",background:T.redBg,color:T.red,borderRadius:8,fontSize:13,marginBottom:"1rem",border:`0.5px solid ${T.red}`}}>⚠️ {error}</div>}

      {accepted && (
        <div style={{padding:"12px 16px",background:T.greenBg,color:T.green,borderRadius:10,fontSize:13,marginBottom:"1rem",border:`0.5px solid ${T.green}`,fontWeight:500}}>
          ✓ Offer accepted — {accepted} will contact you within 24 hours.
        </div>
      )}

      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(280px,1fr))",gap:14}}>
        {eligible.map(offer => (
          <div key={offer.lender} style={{background:T.surface,border:`0.5px solid ${offer.featured?T.green:T.border}`,borderRadius:12,padding:"1.25rem",position:"relative"}}>
            {offer.tag && (
              <div style={{position:"absolute",top:12,right:12,fontSize:10,color:offer.featured?T.green:T.muted,background:offer.featured?T.greenBg:"rgba(136,136,136,0.1)",padding:"2px 8px",borderRadius:20,fontWeight:500}}>
                {offer.tag}
              </div>
            )}
            <div style={{fontSize:13,fontWeight:500,color:T.text,marginBottom:4,paddingRight:60}}>{offer.lender}</div>
            <div style={{fontSize:30,fontWeight:500,color:T.text,margin:"0.5rem 0 0.25rem"}}>{fmt(offer.amount)}</div>
            <div style={{fontSize:12,color:T.muted,marginBottom:"1rem"}}>{offer.rate}% p.a. · {emi(offer.amount,offer.rate,offer.tenure)}</div>

            <div style={{display:"flex",justifyContent:"space-between",fontSize:11,color:T.muted,paddingTop:"0.75rem",borderTop:`0.5px solid ${T.border}`,marginBottom:"0.75rem"}}>
              <span>Tenure: {offer.tenure?`${offer.tenure}m`:"Revolving"}</span>
              <span>Processing: {offer.fee}%</span>
            </div>

            <button
              onClick={() => accepted !== offer.lender && handleAccept(offer)}
              disabled={accepting===offer.lender || !!accepted}
              style={{
                width:"100%",padding:"10px",borderRadius:8,fontSize:13,fontWeight:500,cursor:accepted?"default":"pointer",
                background: accepted===offer.lender ? T.green : offer.featured ? T.text : "transparent",
                color: accepted===offer.lender ? "#fff" : offer.featured ? T.bg : T.textSub,
                border: `0.5px solid ${accepted===offer.lender?T.green:offer.featured?T.text:T.border2}`,
                opacity: accepting===offer.lender ? 0.7 : 1,
              }}
            >
              {accepted===offer.lender?"✓ Accepted":accepting===offer.lender?"Processing...":offer.featured?"Accept Offer":"View Details"}
            </button>
          </div>
        ))}
      </div>

      {eligible.length === 0 && (
        <div style={{background:T.surface,border:`0.5px solid ${T.border}`,borderRadius:12,padding:"3rem",textAlign:"center"}}>
          <div style={{fontSize:13,color:T.textSub,marginBottom:8}}>Score improve karo — zyada offers milenge</div>
          <button onClick={() => navigate("/dashboard/score")} style={{padding:"8px 18px",background:"transparent",color:T.green,border:`0.5px solid ${T.green}`,borderRadius:8,fontSize:13,cursor:"pointer"}}>
            Score Dekho →
          </button>
        </div>
      )}
    </div>
  )
}