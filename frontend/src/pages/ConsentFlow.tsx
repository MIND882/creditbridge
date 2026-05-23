import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { initiateConsent } from '../api/consent'
import { fetchData, computeScore } from '../api/intelligence'
import { useAuthStore } from '../store/authStore'
import { useBusinessStore } from '../store/businessStore'

const T = {
  bg: "#0a0a0f", surface: "#0f0f14", border: "#1a1a1a",
  text: "#f0f0f0", muted: "#555", textSub: "#888",
  green: "#1D9E75", greenBg: "rgba(29,158,117,0.10)",
  red: "#E24B4A",
}

export default function ConsentFlow() {
  const navigate  = useNavigate()
  const { business_id, phone } = useAuthStore()
  const { setScoreData } = useBusinessStore()

  const [step,    setStep]    = useState<'consent' | 'fetching' | 'scoring' | 'done'>('consent')
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')

  const handleStart = async () => {
    setLoading(true)
    setError('')

    try {
      // ── Step 1: Consent ──────────────────────────────
      setStep('consent')
      let needsUpload = false

      try {
        const consentRes = await initiateConsent(business_id!, phone!)
        if (consentRes.data?.status === 'csv_required') {
          needsUpload = true
        }
      } catch {
        // Consent fail → CSV path pe jao but dashboard bhi try karo
        needsUpload = true
      }

      if (needsUpload) {
        // CSV upload pe bhejo — wahan se wapas aayenge
        navigate('/upload')
        return
      }

      // ── Step 2: Fetch bank data ──────────────────────
      setStep('fetching')
      try {
        await fetchData(business_id!)
      } catch {
        // fetchData fail hua — score try karo anyway
        // (bank data already DB mein ho sakta hai)
      }

      // ── Step 3: Compute score ────────────────────────
      setStep('scoring')
      try {
        const res = await computeScore(business_id!)
        if (res.data) {
          setScoreData(res.data)
        }
      } catch {
        // Score compute fail — dashboard pe jao anyway
        // Dashboard apna data khud fetch karega
      }

      // ── Always go to dashboard ───────────────────────
      setStep('done')
      navigate('/dashboard')

    } catch (e: any) {
      setError('Kuch problem aayi. Dashboard pe redirect kar rahe hain...')
      setTimeout(() => navigate('/dashboard'), 2000)
    } finally {
      setLoading(false)
    }
  }

  // ── Skip button — seedha dashboard ──────────────────
  const handleSkip = () => navigate('/dashboard')

  const steps = [
    {
      key: 'consent',
      label: 'Bank data connect karo',
      desc: 'RBI-licensed Account Aggregator se secure connection',
    },
    {
      key: 'fetching',
      label: 'Data fetch ho raha hai',
      desc: '12 mahine ke bank statements pull ho rahe hain',
    },
    {
      key: 'scoring',
      label: 'Score compute ho raha hai',
      desc: 'AI tumhara business pattern analyze kar raha hai',
    },
  ]

  const currentIdx = steps.findIndex(s => s.key === step)

  return (
    <div style={{
      minHeight: '100vh', background: T.bg, color: T.text,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '2rem', fontFamily: "'DM Mono', monospace",
    }}>
      <div style={{ maxWidth: 480, width: '100%' }}>

        {/* Header */}
        <div style={{ fontSize: 11, letterSpacing: '0.15em', color: T.muted, textTransform: 'uppercase', marginBottom: '2rem' }}>
          CreditBridge
        </div>
        <h2 style={{ fontSize: 26, fontWeight: 500, marginBottom: '0.5rem', color: T.text }}>
          Credit score lao
        </h2>
        <p style={{ color: T.textSub, fontSize: 13, lineHeight: 1.6, marginBottom: '2rem' }}>
          Bank data analyze karke tumhara credit score compute hoga. 30 seconds lagenge.
        </p>

        {/* Steps */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: '1.5rem' }}>
          {steps.map((s, i) => {
            const isActive = s.key === step && loading
            const isDone   = step === 'done' || (loading && currentIdx > i)
            return (
              <div key={s.key} style={{
                display: 'flex', gap: 14, alignItems: 'flex-start',
                padding: '0.875rem 1rem',
                background: isActive ? T.surface : 'transparent',
                border: `0.5px solid ${isActive ? '#333' : T.border}`,
                borderRadius: 10,
                transition: 'all 0.3s',
              }}>
                <div style={{
                  width: 26, height: 26, borderRadius: '50%', flexShrink: 0,
                  background: isDone ? T.green : isActive ? T.text : '#1a1a1a',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 11, fontWeight: 600,
                  color: isDone || isActive ? T.bg : T.muted,
                  transition: 'all 0.3s',
                }}>
                  {isDone ? '✓' : isActive ? '●' : i + 1}
                </div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500, color: isActive ? T.text : isDone ? T.green : '#555' }}>
                    {s.label}
                  </div>
                  <div style={{ fontSize: 11, color: T.muted, marginTop: 2 }}>
                    {s.desc}
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Error */}
        {error && (
          <div style={{
            background: T.red + '18', border: `0.5px solid ${T.red}`,
            borderRadius: 8, padding: '0.75rem 1rem',
            fontSize: 12, color: T.red, marginBottom: '1rem',
          }}>
            {error}
          </div>
        )}

        {/* Main button */}
        <button
          onClick={handleStart}
          disabled={loading}
          style={{
            width: '100%', padding: '13px',
            background: loading ? T.surface : T.text,
            color: loading ? T.textSub : T.bg,
            border: `0.5px solid ${loading ? T.border : T.text}`,
            borderRadius: 8, fontSize: 13, fontWeight: 500,
            cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s',
          }}
        >
          {loading ? 'Processing...' : 'Shuru karo — bank data share karo'}
        </button>

        {/* Skip — direct dashboard */}
        {!loading && (
          <button
            onClick={handleSkip}
            style={{
              width: '100%', padding: '10px',
              background: 'transparent', color: T.muted,
              border: 'none', fontSize: 12,
              cursor: 'pointer', marginTop: 8,
            }}
          >
            Skip → Seedha dashboard jao
          </button>
        )}

        <p style={{ fontSize: 11, color: T.muted, textAlign: 'center', marginTop: '1rem' }}>
          RBI Account Aggregator framework se powered. Data encrypted hai, kabhi sell nahi hoga.
        </p>
      </div>
    </div>
  )
}