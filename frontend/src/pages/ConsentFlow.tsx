import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { initiateConsent } from '../api/consent'
import { fetchData, computeScore } from '../api/intelligence'
import { useAuthStore } from '../store/authStore'
import { useBusinessStore } from '../store/businessStore'

export default function ConsentFlow() {
  const navigate = useNavigate()
  const { business_id, phone } = useAuthStore()
  const setScoreData = useBusinessStore((s) => s.setScoreData)
  const [step, setStep] = useState<'consent' | 'fetching' | 'scoring'>('consent')
  const [loading, setLoading] = useState(false)

  const handleStart = async () => {
  setLoading(true)
  try {
    const consentRes = await initiateConsent(business_id!, phone!)
    
    // Agar CSV required hai toh CSV upload pe bhejo
    if (consentRes.data?.status === 'csv_required') {
      navigate('/upload')
      return
    }
    
    setStep('fetching')
    await fetchData(business_id!)
    setStep('scoring')
    const res = await computeScore(business_id!)
    setScoreData(res.data)
    navigate('/dashboard')
  } catch (e) {
    console.error(e)
    // Bank data nahi hai toh CSV upload pe bhejo
    navigate('/upload')
  } finally { setLoading(false) }
}

  const steps = [
    { key: 'consent', label: 'Share bank data', desc: 'Securely connect via RBI-licensed Account Aggregator' },
    { key: 'fetching', label: 'Fetching data', desc: 'Pulling 12 months of bank statements' },
    { key: 'scoring', label: 'Computing score', desc: 'AI analyzing your business patterns' },
  ]

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
      <div style={{ maxWidth: 480, width: '100%' }}>
        <div style={{ fontSize: 12, letterSpacing: '0.15em', color: '#888', textTransform: 'uppercase', marginBottom: '2rem' }}>CreditBridge</div>
        <h2 style={{ fontSize: 28, fontWeight: 500, marginBottom: '0.75rem' }}>Get your credit score</h2>
        <p style={{ color: '#888', fontSize: 14, lineHeight: 1.6, marginBottom: '2rem' }}>We analyze your bank data to compute a credit score. This takes about 30 seconds.</p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: '2rem' }}>
          {steps.map((s, i) => {
            const isActive = s.key === step
            const isDone = steps.findIndex(x => x.key === step) > i
            return (
              <div key={s.key} style={{ display: 'flex', gap: 16, alignItems: 'flex-start', padding: '1rem', background: isActive ? '#111' : 'transparent', border: `0.5px solid ${isActive ? '#333' : '#1a1a1a'}`, borderRadius: 10 }}>
                <div style={{ width: 28, height: 28, borderRadius: '50%', background: isDone ? '#1D9E75' : isActive ? '#f0f0f0' : '#1a1a1a', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, color: isDone || isActive ? '#0a0a0f' : '#444', flexShrink: 0, fontWeight: 500 }}>
                  {isDone ? '✓' : i + 1}
                </div>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 500, color: isActive ? '#f0f0f0' : '#666' }}>{s.label}</div>
                  <div style={{ fontSize: 12, color: '#555', marginTop: 2 }}>{s.desc}</div>
                </div>
              </div>
            )
          })}
        </div>

        <button onClick={handleStart} disabled={loading}
          style={{ width: '100%', padding: '14px', background: '#f0f0f0', color: '#0a0a0f', border: 'none', borderRadius: 8, fontSize: 14, fontWeight: 500, cursor: loading ? 'not-allowed' : 'pointer' }}>
          {loading ? 'Processing...' : 'Start — share my bank data'}
        </button>
        <p style={{ fontSize: 11, color: '#555', textAlign: 'center', marginTop: '1rem' }}>
          Powered by RBI Account Aggregator framework. Your data is encrypted and never sold.
        </p>
      </div>
    </div>
  )
}