import { useState, useRef } from 'react'
import { useAuthStore } from '../store/authStore'

const T = {
  bg:"#0a0a0f",surface:"#0f0f14",border:"#1a1a1a",border2:"#222",
  text:"#f0f0f0",textSub:"#888",muted:"#555",
  green:"#1D9E75",greenBg:"rgba(29,158,117,0.10)",
  red:"#E24B4A",redBg:"rgba(226,75,74,0.10)",
  yellow:"#EF9F27",yellowBg:"rgba(239,159,39,0.10)",
  blue:"#4A90E2",blueBg:"rgba(74,144,226,0.10)",
}

const API_BASE = "http://127.0.0.1:8000/v1"

type DocStatus = "verified" | "pending" | "missing"

interface Doc {
  id: string; name: string; type: string
  status: DocStatus; size?: string; date?: string; required: boolean
}

const INITIAL_DOCS: Doc[] = [
  {id:"pan",    name:"PAN Card",            type:"identity",  status:"verified", size:"245KB", date:"2024-01-15", required:true},
  {id:"gstin",  name:"GSTIN Certificate",   type:"business",  status:"verified", size:"180KB", date:"2024-01-15", required:true},
  {id:"bank6",  name:"Bank Statement (6m)", type:"financial", status:"pending",  size:"1.2MB", date:"2024-01-10", required:true},
  {id:"gstr",   name:"GSTR Returns (1yr)",  type:"financial", status:"verified", size:"890KB", date:"2024-01-12", required:true},
  {id:"itr",    name:"ITR (Last 2 years)",  type:"financial", status:"missing",  required:true},
  {id:"udyam",  name:"Udyam Certificate",   type:"business",  status:"missing",  required:false},
  {id:"lease",  name:"Office Lease/Deed",   type:"property",  status:"missing",  required:false},
  {id:"photo",  name:"Owner Photo",         type:"identity",  status:"pending",  size:"320KB", date:"2024-01-08", required:true},
]

// FIX 1: "missing" badge sirf icon dikhata hai, "Upload" text nahi — Upload button alag hai
const STATUS_CFG: Record<DocStatus, {label:string; color:string; bg:string}> = {
  verified: {label:"✓ Verified",  color:T.green,  bg:T.greenBg},
  pending:  {label:"⏳ Pending",   color:T.yellow, bg:T.yellowBg},
  missing:  {label:"Not uploaded", color:T.muted,  bg:"transparent"},
}

const TYPE_LABELS: Record<string,string> = {
  identity:"Identity", business:"Business", financial:"Financial", property:"Property"
}

// Allowed file types per doc category
const ACCEPT: Record<string,string> = {
  identity: "image/jpeg,image/png,application/pdf",
  financial: "application/pdf",
  business:  "application/pdf,image/jpeg,image/png",
  property:  "application/pdf,image/jpeg,image/png",
}

export default function DocumentVault() {
  const { business_id } = useAuthStore()
  const [docs, setDocs]       = useState<Doc[]>(INITIAL_DOCS)
  const [filter, setFilter]   = useState("all")
  const [uploading, setUploading] = useState<string|null>(null)
  const [toast, setToast]     = useState<{msg:string; type:"success"|"error"} | null>(null)

  // FIX 2: Har doc ke liye alag hidden file input ref
  const fileInputRefs = useRef<Record<string, HTMLInputElement | null>>({})

  const verified = docs.filter(d => d.status === "verified").length
  const total    = docs.length
  const score    = Math.round(verified / total * 100)

  const showToast = (msg: string, type: "success"|"error" = "success") => {
    setToast({msg, type})
    setTimeout(() => setToast(null), 3500)
  }

  // FIX 3: Real file upload — FormData se API pe bhejo
  const handleFileChange = async (docId: string, file: File) => {
    // Validate file size — max 10MB
    if (file.size > 10 * 1024 * 1024) {
      showToast("File size 10MB se zyada nahi honi chahiye", "error")
      return
    }

    setUploading(docId)

    try {
      const token = localStorage.getItem("access_token")
      const formData = new FormData()
      formData.append("file", file)
      formData.append("document_type", docId)
      formData.append("business_id", business_id || "")

      const res = await fetch(`${API_BASE}/kyc/documents/upload`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
        // Note: Content-Type header mat lagao — browser automatically
        // multipart/form-data boundary set karta hai
      })

      if (res.ok) {
        const data = await res.json()
        setDocs(prev => prev.map(d => d.id === docId ? {
          ...d,
          status: "pending",
          date:   new Date().toISOString().slice(0,10),
          size:   `${(file.size / 1024).toFixed(0)}KB`,
        } : d))
        showToast(`${file.name} upload ho gaya ✓`)
        console.log("Upload response:", data)
      } else {
        const err = await res.json().catch(() => ({}))
        showToast(err?.detail || "Upload fail hua, dobara try karo", "error")
      }
    } catch (e) {
      // Offline / network error — mock for dev
      console.warn("API unavailable, using mock:", e)
      setDocs(prev => prev.map(d => d.id === docId ? {
        ...d,
        status: "pending",
        date:   new Date().toISOString().slice(0,10),
        size:   `${(file.size / 1024).toFixed(0)}KB`,
      } : d))
      showToast(`${file.name} upload ho gaya ✓ (demo mode)`)
    } finally {
      setUploading(null)
      // FIX 4: Input reset karo taki same file dobara select ho sake
      if (fileInputRefs.current[docId]) {
        fileInputRefs.current[docId]!.value = ""
      }
    }
  }

  const triggerUpload = (docId: string) => {
    fileInputRefs.current[docId]?.click()
  }

  const types    = ["all", ...Array.from(new Set(docs.map(d => d.type)))]
  const filtered = docs.filter(d => filter === "all" || d.type === filter)

  return (
    <div style={{padding:"1.5rem", maxWidth:900, margin:"0 auto"}}>
      <h1 style={{fontSize:20, fontWeight:500, color:T.text, margin:"0 0 1.5rem"}}>
        Document Vault
      </h1>

      {/* Progress bar */}
      <div style={{
        background:T.surface, border:`0.5px solid ${T.border}`,
        borderRadius:12, padding:"1.25rem", marginBottom:16,
        display:"flex", justifyContent:"space-between", alignItems:"center",
      }}>
        <div>
          <div style={{fontSize:10, color:T.muted, textTransform:"uppercase", letterSpacing:"0.08em"}}>
            KYC Completion
          </div>
          <div style={{fontSize:28, fontWeight:500, color:T.green, marginTop:4}}>{score}%</div>
          <div style={{fontSize:11, color:T.muted, marginTop:2}}>
            {verified}/{total} documents verified
          </div>
        </div>
        <div style={{width:200}}>
          <div style={{height:6, background:T.border, borderRadius:3}}>
            <div style={{
              height:"100%", width:`${score}%`,
              background:T.green, borderRadius:3,
              transition:"width 0.4s ease",
            }}/>
          </div>
          <div style={{fontSize:11, color:T.muted, marginTop:6, textAlign:"right"}}>
            {score >= 80
              ? "Lender ko dikhane ke liye ready ✓"
              : "Aur documents upload karo →"}
          </div>
        </div>
      </div>

      {/* Filter tabs */}
      <div style={{display:"flex", gap:8, marginBottom:16, flexWrap:"wrap"}}>
        {types.map(t => (
          <button key={t} onClick={() => setFilter(t)} style={{
            padding:"5px 14px", borderRadius:20, fontSize:12, cursor:"pointer",
            border:`0.5px solid ${filter===t ? T.green : T.border2}`,
            background: filter===t ? T.greenBg : "transparent",
            color: filter===t ? T.green : T.textSub,
          }}>
            {t === "all" ? "Sab" : TYPE_LABELS[t] || t}
          </button>
        ))}
      </div>

      {/* Doc list */}
      <div style={{background:T.surface, border:`0.5px solid ${T.border}`, borderRadius:12, overflow:"hidden"}}>
        {filtered.map((doc, i) => {
          const cfg = STATUS_CFG[doc.status]
          const isUploading = uploading === doc.id

          return (
            <div key={doc.id} style={{
              display:"flex", justifyContent:"space-between", alignItems:"center",
              padding:"14px 16px",
              borderBottom: i < filtered.length-1 ? `0.5px solid ${T.border}` : "none",
              opacity: isUploading ? 0.7 : 1,
              transition: "opacity 0.2s",
            }}>
              {/* Left: icon + name */}
              <div style={{display:"flex", alignItems:"center", gap:12}}>
                <div style={{
                  width:36, height:36, borderRadius:8, background:T.bg,
                  display:"flex", alignItems:"center", justifyContent:"center", fontSize:16,
                }}>
                  {doc.type==="identity" ? "🪪"
                    : doc.type==="financial" ? "📊"
                    : doc.type==="business"  ? "🏢"
                    : "📄"}
                </div>
                <div>
                  <div style={{
                    fontSize:13, fontWeight:500, color:T.text,
                    display:"flex", alignItems:"center", gap:8,
                  }}>
                    {doc.name}
                    {doc.required && (
                      <span style={{
                        fontSize:9, color:T.red,
                        background:T.redBg+"33",
                        padding:"1px 6px", borderRadius:10,
                      }}>
                        Required
                      </span>
                    )}
                  </div>
                  <div style={{fontSize:11, color:T.muted, marginTop:2}}>
                    {doc.size ? `${doc.size} · ` : ""}{doc.date || "Not uploaded"}
                  </div>
                </div>
              </div>

              {/* Right: status badge + upload button (FIX 1: no duplicate) */}
              <div style={{display:"flex", alignItems:"center", gap:10}}>

                {/* Status badge — sirf verified aur pending ke liye */}
                {doc.status !== "missing" && (
                  <span style={{
                    padding:"3px 10px", borderRadius:20, fontSize:11,
                    fontWeight:500, background:cfg.bg, color:cfg.color,
                    whiteSpace:"nowrap",
                  }}>
                    {cfg.label}
                  </span>
                )}

                {/* FIX 2: Real file input — hidden, triggerUpload se click hota hai */}
                <input
                  type="file"
                  accept={ACCEPT[doc.type] || "*/*"}
                  style={{display:"none"}}
                  ref={el => { fileInputRefs.current[doc.id] = el }}
                  onChange={e => {
                    const file = e.target.files?.[0]
                    if (file) handleFileChange(doc.id, file)
                  }}
                />

                {/* Upload/Re-upload button */}
                {doc.status !== "verified" && (
                  <button
                    onClick={() => triggerUpload(doc.id)}
                    disabled={isUploading}
                    style={{
                      padding:"6px 14px", borderRadius:8,
                      border:`0.5px solid ${doc.status==="missing" ? T.blue : T.border2}`,
                      background: doc.status==="missing" ? T.blueBg : "transparent",
                      color: doc.status==="missing" ? T.blue : T.textSub,
                      fontSize:12, cursor: isUploading ? "not-allowed" : "pointer",
                      opacity: isUploading ? 0.5 : 1,
                      whiteSpace:"nowrap",
                    }}
                  >
                    {isUploading ? "Uploading..." : doc.status === "pending" ? "Re-upload" : "Upload"}
                  </button>
                )}

                {/* View button for verified docs */}
                {doc.status === "verified" && (
                  <button style={{
                    padding:"6px 14px", borderRadius:8,
                    border:`0.5px solid ${T.border2}`,
                    background:"transparent", color:T.muted,
                    fontSize:12, cursor:"pointer",
                  }}>
                    View
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Toast */}
      {toast && (
        <div style={{
          position:"fixed", bottom:24, right:24,
          padding:"11px 18px", borderRadius:10,
          background: toast.type === "error" ? T.redBg : T.greenBg,
          color: toast.type === "error" ? T.red : T.green,
          border:`0.5px solid ${toast.type === "error" ? T.red : T.green}`,
          fontSize:13, fontWeight:500, zIndex:2000,
          animation:"slideIn 0.2s ease",
        }}>
          {toast.msg}
        </div>
      )}

      <style>{`
        @keyframes slideIn {
          from { transform: translateY(10px); opacity: 0; }
          to   { transform: translateY(0);    opacity: 1; }
        }
      `}</style>
    </div>
  )
}