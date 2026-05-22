import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { setApiKey } from '../api/client'
import { getSegments } from '../api/lender'

export default function Login() {
  const navigate = useNavigate()
  const [key, setKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async () => {
    if (!key.trim()) return
    setLoading(true)
    setError('')
    try {
      setApiKey(key.trim())
      await getSegments()  // Validate key
      navigate('/pool')
    } catch {
      setError('Invalid API key. Contact CreditBridge.')
      localStorage.removeItem('lender_api_key')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#080c10'
    }}>
      <div style={{ width: 420, padding: '2.5rem' }}>

        <div style={{
          fontSize: 11,
          letterSpacing: '0.2em',
          color: '#4a9eff',
          textTransform: 'uppercase',
          marginBottom: '0.75rem',
          fontFamily: 'monospace'
        }}>
          CreditBridge
        </div>

        <h1 style={{
          fontSize: 28,
          fontWeight: 600,
          color: '#f1f5f9',
          marginBottom: '0.5rem',
          letterSpacing: '-0.02em'
        }}>
          Lender Console
        </h1>

        <p style={{
          fontSize: 13,
          color: '#64748b',
          marginBottom: '2.5rem',
          lineHeight: 1.6
        }}>
          Access your MSME credit pool and underwriting dashboard.
        </p>

        <div style={{ marginBottom: '1rem' }}>
          <div style={{
            fontSize: 11,
            color: '#64748b',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            marginBottom: '0.5rem'
          }}>
            API Key
          </div>
          <input
            value={key}
            onChange={e => setKey(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleLogin()}
            placeholder="cb_live_..."
            style={{
              width: '100%',
              padding: '12px 14px',
              background: '#0f1520',
              border: '1px solid #1e293b',
              borderRadius: 8,
              color: '#4a9eff',
              fontSize: 13,
              fontFamily: 'monospace',
              outline: 'none',
              letterSpacing: '0.05em'
            }}
          />
        </div>

        {error && (
          <div style={{
            fontSize: 12,
            color: '#ef4444',
            marginBottom: '1rem',
            padding: '8px 12px',
            background: 'rgba(239,68,68,0.1)',
            borderRadius: 6,
            border: '1px solid rgba(239,68,68,0.2)'
          }}>
            {error}
          </div>
        )}

        <button
          onClick={handleLogin}
          disabled={loading || !key}
          style={{
            width: '100%',
            padding: '12px',
            background: loading ? '#1e293b' : '#4a9eff',
            color: loading ? '#64748b' : '#080c10',
            border: 'none',
            borderRadius: 8,
            fontSize: 13,
            fontWeight: 600,
            cursor: loading ? 'not-allowed' : 'pointer',
            fontFamily: 'monospace',
            letterSpacing: '0.05em'
          }}>
          {loading ? 'Verifying...' : 'Access Console →'}
        </button>

        <div style={{
          marginTop: '2rem',
          padding: '1rem',
          background: '#0f1520',
          borderRadius: 8,
          border: '1px solid #1e293b'
        }}>
          {[
            ['820', 'Avg Pool Score'],
            ['₹80L', 'Avg Credit Limit'],
            ['0%', 'Bounce Rate'],
          ].map(([val, label]) => (
            <div key={label} style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginBottom: 8,
              fontSize: 12
            }}>
              <span style={{ color: '#64748b' }}>{label}</span>
              <span style={{ color: '#4a9eff', fontFamily: 'monospace' }}>{val}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}