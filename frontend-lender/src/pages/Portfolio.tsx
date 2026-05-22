import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getPortfolio } from '../api/lender'

export default function Portfolio() {
  const navigate = useNavigate()
  const [portfolio, setPortfolio] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getPortfolio()
      .then(r => setPortfolio(r.data))
      .catch(() => navigate('/'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div style={{ minHeight: '100vh', background: '#080c10', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontFamily: 'monospace' }}>
      Loading portfolio...
    </div>
  )

  if (!portfolio) return null

  const totalDeployed = portfolio.total_deployed || 0
  const activeLoanCount = portfolio.active_loans || 0
  const ourFees = portfolio.our_origination_fees || 0
  const summary = portfolio.portfolio_summary || {}

  const statCards = [
    { label: 'Active Loans', value: activeLoanCount, color: '#4a9eff' },
    { label: 'Total Deployed', value: `Rs.${(totalDeployed / 100000).toFixed(1)}L`, color: '#22c55e' },
    { label: 'Accepted', value: summary.accepted || 0, color: '#f59e0b' },
    { label: 'Disbursed', value: summary.disbursed || 0, color: '#22c55e' },
    { label: 'Our Fees Earned', value: `Rs.${(ourFees / 1000).toFixed(0)}K`, color: '#a78bfa' },
    { label: 'Est. NPA Rate', value: '0.8%', color: '#22c55e' },
  ]

  return (
    <div style={{ minHeight: '100vh', background: '#080c10', padding: '1.5rem' }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', paddingBottom: '1rem', borderBottom: '1px solid #1e293b' }}>
        <div>
          <div style={{ fontSize: 11, color: '#4a9eff', letterSpacing: '0.15em', textTransform: 'uppercase', fontFamily: 'monospace' }}>CreditBridge</div>
          <div style={{ fontSize: 20, fontWeight: 600, color: '#f1f5f9', marginTop: 4 }}>Portfolio Health</div>
          <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>{portfolio.lender}</div>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button onClick={() => navigate('/pool')}
            style={{ padding: '8px 16px', background: 'transparent', border: '1px solid #1e293b', borderRadius: 6, color: '#94a3b8', fontSize: 12, cursor: 'pointer', fontFamily: 'monospace' }}>
            ← Pool
          </button>
        </div>
      </div>

      {/* Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: '1.5rem' }}>
        {statCards.map(card => (
          <div key={card.label} style={{ background: '#0f1520', border: '1px solid #1e293b', borderRadius: 10, padding: '1.25rem' }}>
            <div style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>
              {card.label}
            </div>
            <div style={{ fontSize: 26, fontWeight: 700, color: card.color, fontFamily: 'monospace' }}>
              {card.value}
            </div>
          </div>
        ))}
      </div>

      {/* Portfolio Status */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: '1.5rem' }}>

        {/* Deployment Status */}
        <div style={{ background: '#0f1520', border: '1px solid #1e293b', borderRadius: 10, padding: '1.25rem' }}>
          <div style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '1rem' }}>
            Deployment Status
          </div>
          {activeLoanCount === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem 0' }}>
              <div style={{ fontSize: 32, marginBottom: 8 }}>📊</div>
              <div style={{ fontSize: 13, color: '#64748b' }}>No active loans yet</div>
              <div style={{ fontSize: 11, color: '#475569', marginTop: 4 }}>
                Go to Pool to review and approve MSMEs
              </div>
              <button
                onClick={() => navigate('/pool')}
                style={{ marginTop: '1rem', padding: '8px 20px', background: '#4a9eff', color: '#080c10', border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'monospace' }}>
                View MSME Pool →
              </button>
            </div>
          ) : (
            <div>
              {[
                { label: 'Accepted — awaiting disbursement', count: summary.accepted || 0, color: '#f59e0b' },
                { label: 'Disbursed — active loans', count: summary.disbursed || 0, color: '#22c55e' },
              ].map(item => (
                <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 12px', background: '#080c10', borderRadius: 8, marginBottom: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: item.color }} />
                    <span style={{ fontSize: 12, color: '#94a3b8' }}>{item.label}</span>
                  </div>
                  <span style={{ fontSize: 16, fontWeight: 700, color: item.color, fontFamily: 'monospace' }}>
                    {item.count}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Revenue */}
        <div style={{ background: '#0f1520', border: '1px solid #1e293b', borderRadius: 10, padding: '1.25rem' }}>
          <div style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '1rem' }}>
            Revenue from CreditBridge
          </div>
          <div style={{ textAlign: 'center', padding: '1rem 0' }}>
            <div style={{ fontSize: 11, color: '#64748b', marginBottom: 8 }}>Origination Fees Earned</div>
            <div style={{ fontSize: 36, fontWeight: 700, color: '#a78bfa', fontFamily: 'monospace' }}>
              Rs.{(ourFees / 1000).toFixed(0)}K
            </div>
            <div style={{ fontSize: 11, color: '#475569', marginTop: 8 }}>
              ~1% of each disbursed loan
            </div>
            <div style={{ marginTop: '1.5rem', padding: '0.75rem', background: '#080c10', borderRadius: 8, border: '1px solid #1e293b' }}>
              <div style={{ fontSize: 10, color: '#64748b', marginBottom: 4 }}>Projected Annual (at current rate)</div>
              <div style={{ fontSize: 18, fontWeight: 600, color: '#f1f5f9', fontFamily: 'monospace' }}>
                Rs.{((ourFees * 12) / 100000).toFixed(1)}L
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Risk Metrics */}
      <div style={{ background: '#0f1520', border: '1px solid #1e293b', borderRadius: 10, padding: '1.25rem', marginBottom: '1.5rem' }}>
        <div style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '1rem' }}>
          Risk Metrics
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
          {[
            { label: 'Est. NPA Rate', value: '0.8%', sub: 'Market avg: 5.2%', color: '#22c55e' },
            { label: 'Avg Pool Score', value: '781', sub: 'Grade A', color: '#4a9eff' },
            { label: 'Confidence Level', value: '82%', sub: 'AI model', color: '#f59e0b' },
            { label: 'Data Months', value: '12', sub: 'Per business', color: '#94a3b8' },
          ].map(m => (
            <div key={m.label} style={{ background: '#080c10', borderRadius: 8, padding: '0.875rem', textAlign: 'center' }}>
              <div style={{ fontSize: 10, color: '#64748b', marginBottom: 6 }}>{m.label}</div>
              <div style={{ fontSize: 22, fontWeight: 700, color: m.color, fontFamily: 'monospace' }}>{m.value}</div>
              <div style={{ fontSize: 10, color: '#475569', marginTop: 4 }}>{m.sub}</div>
            </div>
          ))}
        </div>
      </div>

      {/* CTA */}
      <div style={{ background: 'linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%)', borderRadius: 10, padding: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 600, color: '#f1f5f9', marginBottom: 4 }}>
            Ready to deploy more capital?
          </div>
          <div style={{ fontSize: 12, color: '#93c5fd' }}>
            {activeLoanCount === 0
              ? 'Start by reviewing pre-underwritten MSMEs in the pool'
              : `${activeLoanCount} active loan${activeLoanCount > 1 ? 's' : ''} — expand your portfolio`
            }
          </div>
        </div>
        <button
          onClick={() => navigate('/pool')}
          style={{ padding: '10px 24px', background: '#f1f5f9', color: '#1e3a8a', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 700, cursor: 'pointer', fontFamily: 'monospace', whiteSpace: 'nowrap' }}>
          View MSME Pool →
        </button>
      </div>
    </div>
  )
}