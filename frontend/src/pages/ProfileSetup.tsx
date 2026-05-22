import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

const T = {
  bg: "#0a0a0f", surface: "#0f0f14", border: "#1a1a1a", border2: "#222",
  text: "#f0f0f0", textSub: "#888", muted: "#555",
  green: "#1D9E75", greenBg: "rgba(29,158,117,0.10)",
  red: "#E24B4A", redBg: "rgba(226,75,74,0.10)",
  yellow: "#EF9F27", yellowBg: "rgba(239,159,39,0.10)",
}

const API_BASE = "http://127.0.0.1:8000/v1"
const getAuthHeader = (): Record<string, string> => {
  const token = localStorage.getItem("access_token")
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// ─── KYC Status Badge ─────────────────────────────────────────────────────────
const KYCBadge = ({ status }: { status: "idle" | "loading" | "verified" | "failed" }) => {
  const cfg = {
    idle:     { label: "Not verified",  color: T.muted,   bg: "transparent" },
    loading:  { label: "Verifying...",  color: T.yellow,  bg: T.yellowBg },
    verified: { label: "✓ Verified",    color: T.green,   bg: T.greenBg },
    failed:   { label: "✗ Failed",      color: T.red,     bg: T.redBg },
  }[status]

  return (
    <span style={{
      padding: "3px 10px", borderRadius: 20, fontSize: 11,
      fontWeight: 500, background: cfg.bg, color: cfg.color,
      border: `0.5px solid ${cfg.color}`,
    }}>
      {cfg.label}
    </span>
  )
}

export default function ProfileSetup() {
  const navigate = useNavigate()
  const { business_id } = useAuthStore()

  // Form state
  const [pan, setPan]   = useState("")
  const [gstin, setGstin] = useState("")
  const [mobile, setMobile] = useState("")
  const [businessName, setBusinessName] = useState("")

  // KYC state
  const [panStatus,   setPanStatus]   = useState<"idle"|"loading"|"verified"|"failed">("idle")
  const [gstinStatus, setGstinStatus] = useState<"idle"|"loading"|"verified"|"failed">("idle")

  // Verified data
  const [panData,   setPanData]   = useState<any>(null)
  const [gstinData, setGstinData] = useState<any>(null)

  const [saving, setSaving] = useState(false)
  const [error,  setError]  = useState<string | null>(null)

  // ── PAN Verify ──────────────────────────────────────────────────────────────
  const verifyPAN = async () => {
    if (pan.length !== 10) { setError("PAN 10 characters ka hona chahiye"); return }
    setPanStatus("loading"); setError(null)
    try {
      const res = await fetch(`${API_BASE}/kyc/pan`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...getAuthHeader() },
        body: JSON.stringify({ pan_number: pan.toUpperCase() }),
      })
      const data = await res.json()
      if (res.ok && data.verified) {
        setPanStatus("verified")
        setPanData(data)
        // Auto-fill name if empty
        if (!businessName && data.full_name) setBusinessName(data.full_name)
      } else {
        setPanStatus("failed")
        setError(data.detail || "PAN verify nahi hua")
      }
    } catch {
      setPanStatus("failed")
      setError("Network error")
    }
  }

  // ── GSTIN Verify ────────────────────────────────────────────────────────────
  const verifyGSTIN = async () => {
    if (gstin.length !== 15) { setError("GSTIN 15 characters ka hona chahiye"); return }
    setGstinStatus("loading"); setError(null)
    try {
      const res = await fetch(`${API_BASE}/kyc/gstin`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...getAuthHeader() },
        body: JSON.stringify({ gstin: gstin.toUpperCase() }),
      })
      const data = await res.json()
      if (res.ok && data.verified) {
        setGstinStatus("verified")
        setGstinData(data)
        if (!businessName && data.legal_name) setBusinessName(data.legal_name)
      } else {
        setGstinStatus("failed")
        setError(data.detail || "GSTIN verify nahi hua")
      }
    } catch {
      setGstinStatus("failed")
      setError("Network error")
    }
  }

  // ── Save Profile ─────────────────────────────────────────────────────────────
  const handleSave = async () => {
    if (panStatus !== "verified") { setError("PAN verify karna zaroori hai"); return }
    setSaving(true); setError(null)
    try {
      await fetch(`${API_BASE}/businesses/${business_id}/profile`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...getAuthHeader() },
        body: JSON.stringify({
          pan_number:    pan.toUpperCase(),
          gstin:         gstin.toUpperCase() || null,
          mobile:        mobile,
          business_name: businessName,
          pan_verified:  true,
          gstin_verified: gstinStatus === "verified",
          kyc_score:     panData ? (gstinStatus === "verified" ? 85 : 60) : 0,
        }),
      })
      navigate("/dashboard")
    } catch {
      // Mock save — still go to dashboard
      navigate("/dashboard")
    } finally {
      setSaving(false)
    }
  }

  const inp: React.CSSProperties = {
    flex: 1, padding: "10px 14px", borderRadius: 8,
    border: `0.5px solid ${T.border2}`, background: T.bg,
    color: T.text, fontSize: 14, outline: "none",
    textTransform: "uppercase" as const,
  }

  const btn = (color: string, bg: string, disabled = false): React.CSSProperties => ({
    padding: "10px 18px", borderRadius: 8, border: `0.5px solid ${color}`,
    background: disabled ? "transparent" : bg, color: disabled ? T.muted : color,
    cursor: disabled ? "not-allowed" : "pointer", fontSize: 13,
    fontWeight: 500, whiteSpace: "nowrap" as const, flexShrink: 0,
  })

  const kycDone = panStatus === "verified"
  const kycScore = kycDone ? (gstinStatus === "verified" ? 85 : 60) : 0

  return (
    <div style={{ padding: "2rem", maxWidth: 600, margin: "0 auto" }}>

      {/* Header */}
      <div style={{ marginBottom: "2rem" }}>
        <h1 style={{ margin: 0, fontSize: 20, fontWeight: 500, color: T.text }}>
          Business Profile Setup
        </h1>
        <p style={{ margin: "6px 0 0", fontSize: 13, color: T.muted }}>
          KYC verification — loan ke liye zaroori hai
        </p>
      </div>

      {/* KYC Score Bar */}
      {kycScore > 0 && (
        <div style={{
          background: T.surface, border: `0.5px solid ${T.border}`,
          borderRadius: 12, padding: "1rem 1.25rem", marginBottom: "1.5rem",
          display: "flex", alignItems: "center", justifyContent: "space-between",
        }}>
          <div>
            <div style={{ fontSize: 11, color: T.muted, textTransform: "uppercase", letterSpacing: "0.06em" }}>
              KYC Trust Score
            </div>
            <div style={{ fontSize: 28, fontWeight: 500, color: T.green, marginTop: 4 }}>
              {kycScore}/100
            </div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 12, color: T.muted }}>
              {gstinStatus === "verified" ? "PAN + GSTIN verified ✓" : "PAN verified ✓"}
            </div>
            <div style={{ fontSize: 11, color: T.muted, marginTop: 4 }}>
              {gstinStatus === "verified" ? "Lender ready hai" : "GSTIN verify karo score badhane ke liye"}
            </div>
          </div>
        </div>
      )}

      {/* Form */}
      <div style={{
        background: T.surface, border: `0.5px solid ${T.border}`,
        borderRadius: 12, padding: "1.5rem",
        display: "flex", flexDirection: "column", gap: "1.25rem",
      }}>

        {/* PAN Field */}
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <label style={{ fontSize: 11, color: T.muted, textTransform: "uppercase", letterSpacing: "0.06em" }}>
              PAN Number *
            </label>
            <KYCBadge status={panStatus} />
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <input
              style={inp}
              placeholder="ABCDE1234F"
              value={pan}
              maxLength={10}
              onChange={e => { setPan(e.target.value.toUpperCase()); setPanStatus("idle") }}
            />
            <button
              onClick={verifyPAN}
              disabled={pan.length !== 10 || panStatus === "loading"}
              style={btn(T.green, T.greenBg, pan.length !== 10 || panStatus === "loading")}
            >
              {panStatus === "loading" ? "..." : "Verify"}
            </button>
          </div>

          {/* PAN Result */}
          {panData && panStatus === "verified" && (
            <div style={{
              marginTop: 10, padding: "10px 12px", borderRadius: 8,
              background: T.greenBg, border: `0.5px solid ${T.green}`,
            }}>
              <div style={{ fontSize: 13, color: T.green, fontWeight: 500 }}>
                {panData.full_name}
              </div>
              <div style={{ fontSize: 11, color: T.green, marginTop: 3, opacity: 0.8 }}>
                Aadhaar linked: {panData.aadhaar_linked ? "✓ Haan" : "✗ Nahi"}
                {panData.gender ? ` · ${panData.gender === "M" ? "Male" : "Female"}` : ""}
              </div>
            </div>
          )}
        </div>

        {/* GSTIN Field */}
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <label style={{ fontSize: 11, color: T.muted, textTransform: "uppercase", letterSpacing: "0.06em" }}>
              GSTIN <span style={{ color: T.muted, fontWeight: 400 }}>(optional — score badhata hai)</span>
            </label>
            <KYCBadge status={gstinStatus} />
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <input
              style={{ ...inp, textTransform: "uppercase" }}
              placeholder="27AAPFU0939F1ZV"
              value={gstin}
              maxLength={15}
              onChange={e => { setGstin(e.target.value.toUpperCase()); setGstinStatus("idle") }}
            />
            <button
              onClick={verifyGSTIN}
              disabled={gstin.length !== 15 || gstinStatus === "loading"}
              style={btn(T.green, T.greenBg, gstin.length !== 15 || gstinStatus === "loading")}
            >
              {gstinStatus === "loading" ? "..." : "Verify"}
            </button>
          </div>

          {/* GSTIN Result */}
          {gstinData && gstinStatus === "verified" && (
            <div style={{
              marginTop: 10, padding: "10px 12px", borderRadius: 8,
              background: T.greenBg, border: `0.5px solid ${T.green}`,
            }}>
              <div style={{ fontSize: 13, color: T.green, fontWeight: 500 }}>
                {gstinData.legal_name}
              </div>
              <div style={{ fontSize: 11, color: T.green, marginTop: 3, opacity: 0.8 }}>
                Status: {gstinData.gstin_status} · {gstinData.state}
              </div>
            </div>
          )}
        </div>

        {/* Mobile */}
        <div>
          <label style={{ fontSize: 11, color: T.muted, textTransform: "uppercase", letterSpacing: "0.06em", display: "block", marginBottom: 8 }}>
            Mobile Number
          </label>
          <input
            style={{ ...inp, textTransform: "none" as const, width: "100%", boxSizing: "border-box" as const }}
            placeholder="+91 98765 43210"
            value={mobile}
            onChange={e => setMobile(e.target.value)}
          />
        </div>

        {/* Business Name (auto-filled) */}
        <div>
          <label style={{ fontSize: 11, color: T.muted, textTransform: "uppercase", letterSpacing: "0.06em", display: "block", marginBottom: 8 }}>
            Business Name
          </label>
          <input
            style={{ ...inp, textTransform: "none" as const, width: "100%", boxSizing: "border-box" as const }}
            placeholder="Auto-filled from PAN/GSTIN"
            value={businessName}
            onChange={e => setBusinessName(e.target.value)}
          />
        </div>

        {/* Error */}
        {error && (
          <div style={{
            padding: "10px 12px", borderRadius: 8,
            background: T.redBg, color: T.red,
            border: `0.5px solid ${T.red}`, fontSize: 13,
          }}>
            ⚠️ {error}
          </div>
        )}

        {/* Save Button */}
        <button
          onClick={handleSave}
          disabled={saving || panStatus !== "verified"}
          style={{
            padding: "12px", borderRadius: 8, border: "none",
            background: panStatus === "verified" ? T.text : T.border2,
            color: panStatus === "verified" ? T.bg : T.muted,
            cursor: panStatus === "verified" ? "pointer" : "not-allowed",
            fontSize: 14, fontWeight: 500, marginTop: 4,
          }}
        >
          {saving ? "Saving..." : panStatus === "verified" ? "Profile Save Karo →" : "Pehle PAN verify karo"}
        </button>
      </div>
    </div>
  )
}
