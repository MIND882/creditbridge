import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { register, login } from '../api/auth'
import { useAuthStore } from '../store/authStore'

const T = {
  bg: "#0a0a0f", surface: "#0f0f14", border: "#1a1a1a", border2: "#222",
  text: "#f0f0f0", textSub: "#888", muted: "#555",
  green: "#1D9E75", greenBg: "rgba(29,158,117,0.10)",
  red: "#E24B4A", redBg: "rgba(226,75,74,0.10)",
  yellow: "#EF9F27", yellowBg: "rgba(239,159,39,0.10)",
}

const API_BASE = "http://127.0.0.1:8000/v1"

type KYCStatus = "idle" | "loading" | "verified" | "failed"

// ─── KYC Badge ────────────────────────────────────────────────────────────────
const KYCBadge = ({ status }: { status: KYCStatus }) => {
  const cfg = {
    idle:     { label: "Verify karo",  color: T.muted,  bg: "transparent" },
    loading:  { label: "Verifying...", color: T.yellow, bg: T.yellowBg },
    verified: { label: "✓ Verified",   color: T.green,  bg: T.greenBg },
    failed:   { label: "✗ Failed",     color: T.red,    bg: T.redBg },
  }[status]
  return (
    <span style={{ padding: "2px 8px", borderRadius: 20, fontSize: 11, fontWeight: 500, background: cfg.bg, color: cfg.color, border: `0.5px solid ${cfg.color}` }}>
      {cfg.label}
    </span>
  )
}

// ─── Step Indicator ───────────────────────────────────────────────────────────
const StepBar = ({ step }: { step: number }) => (
  <div style={{ display: "flex", alignItems: "center", gap: 0, marginBottom: "2rem" }}>
    {["Basic Info", "KYC Verify", "Done"].map((label, i) => {
      const active  = i + 1 === step
      const done    = i + 1 < step
      return (
        <div key={i} style={{ display: "flex", alignItems: "center", flex: i < 2 ? 1 : "none" }}>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
            <div style={{
              width: 28, height: 28, borderRadius: "50%", display: "flex",
              alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 500,
              background: done ? T.green : active ? T.text : "transparent",
              color: done ? "#fff" : active ? T.bg : T.muted,
              border: `1.5px solid ${done ? T.green : active ? T.text : T.border2}`,
            }}>
              {done ? "✓" : i + 1}
            </div>
            <span style={{ fontSize: 10, color: active ? T.text : T.muted, whiteSpace: "nowrap" }}>{label}</span>
          </div>
          {i < 2 && <div style={{ flex: 1, height: 1, background: done ? T.green : T.border2, margin: "0 8px", marginBottom: 16 }} />}
        </div>
      )
    })}
  </div>
)

export default function Register() {
  const navigate  = useNavigate()
  const setAuth   = useAuthStore((s) => s.setAuth)
  const [mode, setMode]     = useState<"register" | "login">("register")
  const [step, setStep]     = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState("")

  // Form data
  const [form, setForm] = useState({
    pan: "", gstin: "", business_name: "", owner_name: "",
    owner_phone: "", owner_email: "", business_type: "textile",
    city: "", state: "",
  })

  // KYC state
  const [panStatus,   setPanStatus]   = useState<KYCStatus>("idle")
  const [gstinStatus, setGstinStatus] = useState<KYCStatus>("idle")
  const [panData,     setPanData]     = useState<any>(null)
  const [gstinData,   setGstinData]   = useState<any>(null)

  const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }))

  // ── Step 1 Validate ──────────────────────────────────────────────────────────
  const goToKYC = () => {
    if (!form.owner_phone || !form.owner_name || !form.business_name) {
      setError("Phone, naam aur business naam zaroori hai"); return
    }
    if (form.owner_phone.length < 10) {
      setError("Valid phone number daalo"); return
    }
    setError(""); setStep(2)
  }

  // ── PAN Verify ───────────────────────────────────────────────────────────────
  const verifyPAN = async () => {
    if (form.pan.length !== 10) { setError("PAN 10 characters ka hona chahiye"); return }
    setPanStatus("loading"); setError("")
    try {
      const res  = await fetch(`${API_BASE}/kyc/pan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pan_number: form.pan.toUpperCase() }),
      })
      const data = await res.json()
      if (res.ok && data.verified) {
        setPanStatus("verified"); setPanData(data)
        // Auto-fill owner name if empty
        if (!form.owner_name && data.full_name) set("owner_name", data.full_name)
      } else {
        setPanStatus("failed")
        setError(data.detail || "PAN verify nahi hua — dobara check karo")
      }
    } catch {
      setPanStatus("failed"); setError("Network error — server running hai?")
    }
  }

  // ── GSTIN Verify ─────────────────────────────────────────────────────────────
  const verifyGSTIN = async () => {
    if (form.gstin.length !== 15) { setError("GSTIN 15 characters ka hona chahiye"); return }
    setGstinStatus("loading"); setError("")
    try {
      const res  = await fetch(`${API_BASE}/kyc/gstin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ gstin: form.gstin.toUpperCase() }),
      })
      const data = await res.json()
      if (res.ok && data.verified) {
        setGstinStatus("verified"); setGstinData(data)
        if (!form.business_name && data.business_name) set("business_name", data.business_name)
        if (!form.city && data.address)                set("city", data.address.split(",").slice(-3, -2)[0]?.trim() || "")
      } else {
        setGstinStatus("failed")
        setError(data.detail || "GSTIN verify nahi hua")
      }
    } catch {
      setGstinStatus("failed"); setError("Network error")
    }
  }

  // ── Final Register ────────────────────────────────────────────────────────────
  const handleRegister = async () => {
    if (panStatus !== "verified") { setError("PAN verify karna zaroori hai"); return }
    setLoading(true); setError("")
    try {
      const res = await register({
        ...form,
        pan:           form.pan.toUpperCase(),
        gstin:         form.gstin.toUpperCase() || undefined,
        pan_verified:  true,
        gstin_verified: gstinStatus === "verified",
        kyc_score:     panData ? (gstinStatus === "verified" ? 100 : 60) : 0,
      })
      setAuth(res.data.access_token, res.data.business_id, form.owner_phone)
      navigate("/consent")
    } catch (e: any) {
      setError(e.response?.data?.detail || "Registration failed — try again")
    } finally { setLoading(false) }
  }

  // ── Login ─────────────────────────────────────────────────────────────────────
  const handleLogin = async () => {
    setLoading(true); setError("")
    try {
      const res = await login(form.owner_phone)
      setAuth(res.data.access_token, res.data.business_id, form.owner_phone)
      navigate("/dashboard")
    } catch (e: any) {
      setError(e.response?.data?.detail || "Login failed")
    } finally { setLoading(false) }
  }

  // ── Styles ────────────────────────────────────────────────────────────────────
  const inp: React.CSSProperties = {
    background: T.surface, border: `0.5px solid ${T.border2}`,
    borderRadius: 8, padding: "10px 14px", color: T.text,
    fontSize: 14, width: "100%", outline: "none", boxSizing: "border-box",
  }
  const verifyBtn = (disabled: boolean, color = T.green): React.CSSProperties => ({
    padding: "10px 16px", borderRadius: 8, border: `0.5px solid ${disabled ? T.border2 : color}`,
    background: disabled ? "transparent" : `${color}18`, color: disabled ? T.muted : color,
    cursor: disabled ? "not-allowed" : "pointer", fontSize: 13,
    fontWeight: 500, whiteSpace: "nowrap", flexShrink: 0,
  })

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "2rem", background: T.bg }}>
      <div style={{ width: "100%", maxWidth: 460 }}>

        {/* Logo */}
        <div style={{ fontSize: 12, letterSpacing: "0.15em", color: T.textSub, textTransform: "uppercase", marginBottom: "2rem" }}>
          CreditBridge
        </div>

        {/* Mode toggle */}
        <div style={{ display: "flex", gap: 8, marginBottom: "2rem" }}>
          {(["register", "login"] as const).map(m => (
            <button key={m} onClick={() => { setMode(m); setStep(1); setError("") }}
              style={{ flex: 1, padding: "10px", background: mode === m ? T.text : "transparent", color: mode === m ? T.bg : T.textSub, border: `0.5px solid ${T.border2}`, borderRadius: 8, fontSize: 13, cursor: "pointer" }}>
              {m === "register" ? "New business" : "Sign in"}
            </button>
          ))}
        </div>

        {/* ── REGISTER FLOW ─────────────────────────────────────────────────── */}
        {mode === "register" && (
          <>
            <StepBar step={step} />

            {/* STEP 1 — Basic Info */}
            {step === 1 && (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <div style={{ fontSize: 14, fontWeight: 500, color: T.text, marginBottom: 4 }}>
                  Basic Information
                </div>

                {[
                  ["Business name",    "business_name", "Sharma Textiles Pvt Ltd",  "text"],
                  ["Owner name",       "owner_name",    "Rajesh Sharma",             "text"],
                  ["Phone number",     "owner_phone",   "9876543210",                "tel"],
                  ["Email (optional)", "owner_email",   "rajesh@example.com",        "email"],
                  ["City",             "city",          "Surat",                     "text"],
                  ["State",            "state",         "Gujarat",                   "text"],
                ].map(([label, key, placeholder, type]) => (
                  <div key={key}>
                    <div style={{ fontSize: 11, color: T.muted, marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.05em" }}>{label}</div>
                    <input style={inp} type={type} placeholder={placeholder}
                      value={(form as any)[key]}
                      onChange={e => set(key, e.target.value)} />
                  </div>
                ))}

                {error && <div style={{ color: T.red, fontSize: 13, padding: "8px 12px", background: T.redBg, borderRadius: 8 }}>{error}</div>}

                <button onClick={goToKYC} style={{ marginTop: 8, padding: "12px", background: T.text, color: T.bg, border: "none", borderRadius: 8, fontSize: 14, fontWeight: 500, cursor: "pointer" }}>
                  Next — KYC Verify →
                </button>
              </div>
            )}

            {/* STEP 2 — KYC Verification */}
            {step === 2 && (
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <div style={{ fontSize: 14, fontWeight: 500, color: T.text, marginBottom: 4 }}>
                  KYC Verification
                </div>

                {/* KYC Score Preview */}
                {panStatus === "verified" && (
                  <div style={{ background: T.greenBg, border: `0.5px solid ${T.green}`, borderRadius: 10, padding: "12px 16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                      <div style={{ fontSize: 11, color: T.green, textTransform: "uppercase", letterSpacing: "0.05em" }}>KYC Score</div>
                      <div style={{ fontSize: 24, fontWeight: 500, color: T.green, marginTop: 2 }}>
                        {gstinStatus === "verified" ? "100" : "60"}/100
                      </div>
                    </div>
                    <div style={{ fontSize: 12, color: T.green, textAlign: "right" }}>
                      {gstinStatus === "verified" ? "✓ PAN + GSTIN" : "✓ PAN verified"}<br />
                      <span style={{ opacity: 0.7, fontSize: 11 }}>
                        {gstinStatus !== "verified" ? "GSTIN add karo → 100/100" : "Lender ready!"}
                      </span>
                    </div>
                  </div>
                )}

                {/* PAN Field */}
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                    <label style={{ fontSize: 11, color: T.muted, textTransform: "uppercase", letterSpacing: "0.05em" }}>PAN Number *</label>
                    <KYCBadge status={panStatus} />
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <input
                      style={{ ...inp, textTransform: "uppercase" }}
                      placeholder="ABCDE1234F"
                      value={form.pan}
                      maxLength={10}
                      onChange={e => { set("pan", e.target.value.toUpperCase()); setPanStatus("idle") }}
                    />
                    <button
                      onClick={verifyPAN}
                      disabled={form.pan.length !== 10 || panStatus === "loading"}
                      style={verifyBtn(form.pan.length !== 10 || panStatus === "loading")}
                    >
                      {panStatus === "loading" ? "..." : "Verify"}
                    </button>
                  </div>
                  {panData && panStatus === "verified" && (
                    <div style={{ marginTop: 8, padding: "8px 12px", borderRadius: 8, background: T.greenBg, border: `0.5px solid ${T.green}` }}>
                      <div style={{ fontSize: 13, color: T.green, fontWeight: 500 }}>{panData.full_name}</div>
                      <div style={{ fontSize: 11, color: T.green, opacity: 0.8, marginTop: 2 }}>
                        Aadhaar linked: {panData.aadhaar_linked ? "✓ Haan" : "✗ Nahi"}
                        {panData.gender ? ` · ${panData.gender === "M" ? "Male" : "Female"}` : ""}
                      </div>
                    </div>
                  )}
                </div>

                {/* GSTIN Field */}
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                    <label style={{ fontSize: 11, color: T.muted, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                      GSTIN <span style={{ fontWeight: 400, textTransform: "none" }}>(optional — score badhata hai)</span>
                    </label>
                    <KYCBadge status={gstinStatus} />
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <input
                      style={{ ...inp, textTransform: "uppercase" }}
                      placeholder="27AANCR3575R1ZB"
                      value={form.gstin}
                      maxLength={15}
                      onChange={e => { set("gstin", e.target.value.toUpperCase()); setGstinStatus("idle") }}
                    />
                    <button
                      onClick={verifyGSTIN}
                      disabled={form.gstin.length !== 15 || gstinStatus === "loading"}
                      style={verifyBtn(form.gstin.length !== 15 || gstinStatus === "loading")}
                    >
                      {gstinStatus === "loading" ? "..." : "Verify"}
                    </button>
                  </div>
                  {gstinData && gstinStatus === "verified" && (
                    <div style={{ marginTop: 8, padding: "8px 12px", borderRadius: 8, background: T.greenBg, border: `0.5px solid ${T.green}` }}>
                      <div style={{ fontSize: 13, color: T.green, fontWeight: 500 }}>{gstinData.business_name}</div>
                      <div style={{ fontSize: 11, color: T.green, opacity: 0.8, marginTop: 2 }}>
                        {gstinData.gstin_status} · {gstinData.business_type}
                      </div>
                    </div>
                  )}
                </div>

                {error && (
                  <div style={{ color: T.red, fontSize: 13, padding: "8px 12px", background: T.redBg, borderRadius: 8 }}>
                    ⚠️ {error}
                  </div>
                )}

                <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
                  <button onClick={() => { setStep(1); setError("") }}
                    style={{ padding: "12px 20px", background: "transparent", color: T.textSub, border: `0.5px solid ${T.border2}`, borderRadius: 8, fontSize: 13, cursor: "pointer" }}>
                    ← Back
                  </button>
                  <button
                    onClick={handleRegister}
                    disabled={loading || panStatus !== "verified"}
                    style={{
                      flex: 1, padding: "12px",
                      background: panStatus === "verified" ? T.text : T.border2,
                      color: panStatus === "verified" ? T.bg : T.muted,
                      border: "none", borderRadius: 8, fontSize: 14,
                      fontWeight: 500,
                      cursor: panStatus === "verified" ? "pointer" : "not-allowed",
                    }}
                  >
                    {loading ? "Creating account..." : panStatus === "verified" ? "Get my credit score →" : "Pehle PAN verify karo"}
                  </button>
                </div>
              </div>
            )}
          </>
        )}

        {/* ── LOGIN FLOW ────────────────────────────────────────────────────── */}
        {mode === "login" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div>
              <div style={{ fontSize: 11, color: T.muted, marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.05em" }}>Phone number</div>
              <input style={inp} placeholder="9876543210"
                value={form.owner_phone}
                onChange={e => set("owner_phone", e.target.value)} />
            </div>
            {error && <div style={{ color: T.red, fontSize: 13 }}>{error}</div>}
            <button onClick={handleLogin} disabled={loading}
              style={{ marginTop: 8, padding: "12px", background: T.text, color: T.bg, border: "none", borderRadius: 8, fontSize: 14, fontWeight: 500, cursor: "pointer" }}>
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}