import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export default function Landing() {
  const navigate = useNavigate()
  const token = useAuthStore((s) => s.token)

  if (token) navigate('/dashboard')

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
      <div style={{ maxWidth: 520, textAlign: 'center' }}>
        <div style={{ fontSize: 12, letterSpacing: '0.15em', color: '#888', textTransform: 'uppercase', marginBottom: '1.5rem' }}>
          CreditBridge
        </div>
        <h1 style={{ fontSize: 42, fontWeight: 500, lineHeight: 1.15, marginBottom: '1.5rem', color: '#f0f0f0' }}>
          Your business data.<br />Your credit score.
        </h1>
        <p style={{ fontSize: 16, color: '#888', lineHeight: 1.7, marginBottom: '2.5rem' }}>
          Share your bank data securely. Get an instant credit score. Access working capital loans up to ₹80L — in minutes.
        </p>
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
          <button
            onClick={() => navigate('/register')}
            style={{ padding: '12px 32px', background: '#f0f0f0', color: '#0a0a0f', border: 'none', borderRadius: 8, fontSize: 14, fontWeight: 500, cursor: 'pointer' }}>
            Get your score
          </button>
          <button
            onClick={() => navigate('/register')}
            style={{ padding: '12px 32px', background: 'transparent', color: '#f0f0f0', border: '0.5px solid #333', borderRadius: 8, fontSize: 14, cursor: 'pointer' }}>
            Sign in
          </button>
        </div>
        <div style={{ marginTop: '3rem', display: 'flex', gap: '2rem', justifyContent: 'center' }}>
          {[['₹80L', 'Max loan limit'], ['0', 'Hidden fees'], ['3 min', 'To get your score']].map(([val, label]) => (
            <div key={label} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 22, fontWeight: 500, color: '#f0f0f0' }}>{val}</div>
              <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>{label}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}