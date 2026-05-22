import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getBusinessDetail, getExplanation, logRejection } from '../api/lender'

export default function BusinessDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [detail, setDetail] = useState<any>(null)
  const [explain, setExplain] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [decision, setDecision] = useState<string | null>(null)
  const [rejectionReason, setRejectionReason] = useState('')
  const [showReject, setShowReject] = useState(false)

  useEffect(() => {
    Promise.all([
      getBusinessDetail(id!),
      getExplanation(id!)
    ]).then(([d, e]) => {
      setDetail(d.data)
      setExplain(e.data)
    }).finally(() => setLoading(false))
  }, [id])

  const handleReject = async () => {
    if (!rejectionReason) return
    await logRejection({
      business_id: id!,
      rejection_reason: rejectionReason,
      rejection_detail: `Lender rejected via dashboard`
    })
    setDecision('rejected')
    setShowReject(false)
  }

  if (loading) return (
    <div style={{ minHeight: '100vh', background: '#080c10', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontFamily: 'monospace' }}>
      Loading underwriting data...
    </div>
  )

  if (!detail) return null

  const rec = detail.underwriting_recommendation
  const recColor = rec.decision === 'APPROVE' ? '#22c55e' : rec.decision === 'CONDITIONAL' ? '#f59e0b' : '#ef4444'

  return (
    <div style={{ minHeight: '100vh', background: '#080c10', padding: '1.5rem', maxWidth: 1100, margin: '0 auto' }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <button
          onClick={() => navigate('/pool')}
          style={{ fontSize: 12, color: '#4a9eff', background: 'transparent', border: 'none', cursor: 'pointer', fontFamily: 'monospace' }}>
          ← Back to Pool
        </button>
        <div style={{ fontSize: 11, color: '#4a9eff', letterSpacing: '0.15em', textTransform: 'uppercase', fontFamily: 'monospace' }}>
          CreditBridge Underwriting
        </div>
      </div>

      {/* Business Header */}
      <div style={{
        background: '#0f1520',
        border: '1px solid #1e293b',
        borderRadius: 12,
        padding: '1.5rem',
        marginBottom: '1rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <div style={{ fontSize: 22, fontWeight: 600, color: '#f1f5f9' }}>{detail.business.name}</div>
          <div style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>
            {detail.business.owner} · {detail.business.city} · {detail.business.type} · GSTIN: {detail.business.gstin}
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 48, fontWeight: 700, color: recColor, fontFamily: 'monospace', lineHeight: 1 }}>
            {detail.risk_profile.score}
          </div>
          <div style={{ fontSize: 13, color: recColor, marginTop: 4 }}>{detail.risk_profile.grade} Grade</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>

        {/* Recommendation */}
        <div style={{
          background: '#0f1520',
          border: `1px solid ${recColor}40`,
          borderRadius: 12,
          padding: '1.25rem'
        }}>
          <div style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.75rem' }}>
            Underwriting Recommendation
          </div>
          <div style={{ fontSize: 20, fontWeight: 700, color: recColor, fontFamily: 'monospace', marginBottom: 8 }}>
            {rec.decision}
          </div>
          <div style={{ fontSize: 12, color: '#94a3b8', lineHeight: 1.6, marginBottom: '1rem' }}>{rec.reason}</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            <div style={{ background: '#080c10', borderRadius: 8, padding: '0.75rem' }}>
              <div style={{ fontSize: 10, color: '#64748b', marginBottom: 4 }}>Suggested Amount</div>
              <div style={{ fontSize: 16, color: '#22c55e', fontFamily: 'monospace' }}>₹{(rec.suggested_amount / 100000).toFixed(0)}L</div>
            </div>
            <div style={{ background: '#080c10', borderRadius: 8, padding: '0.75rem' }}>
              <div style={{ fontSize: 10, color: '#64748b', marginBottom: 4 }}>Suggested Rate</div>
              <div style={{ fontSize: 16, color: '#4a9eff', fontFamily: 'monospace' }}>{rec.suggested_rate}%</div>
            </div>
          </div>
        </div>

        {/* Score Breakdown */}
        <div style={{ background: '#0f1520', border: '1px solid #1e293b', borderRadius: 12, padding: '1.25rem' }}>
          <div style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.75rem' }}>
            Score Breakdown
          </div>
          {explain?.breakdown?.map((b: any) => (
            <div key={b.factor} style={{ marginBottom: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 4 }}>
                <span style={{ color: '#94a3b8' }}>{b.factor}</span>
                <span style={{ color: '#4a9eff', fontFamily: 'monospace' }}>{b.score}/100 · {b.weight}</span>
              </div>
              <div style={{ height: 3, background: '#1e293b', borderRadius: 2 }}>
                <div style={{
                  width: `${b.score}%`,
                  height: '100%',
                  background: b.score >= 80 ? '#22c55e' : b.score >= 60 ? '#f59e0b' : '#ef4444',
                  borderRadius: 2
                }} />
              </div>
              <div style={{ fontSize: 10, color: '#475569', marginTop: 2 }}>{b.explanation}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Risk Flags + Positives */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
        <div style={{ background: '#0f1520', border: '1px solid #1e293b', borderRadius: 12, padding: '1.25rem' }}>
          <div style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.75rem' }}>Risk Flags</div>
          {detail.risk_profile.flags?.length === 0 ? (
            <div style={{ fontSize: 12, color: '#22c55e' }}>✓ No risk flags</div>
          ) : detail.risk_profile.flags?.map((f: string) => (
            <div key={f} style={{ fontSize: 12, color: '#f59e0b', marginBottom: 6, display: 'flex', gap: 8 }}>
              <span>⚠</span><span>{f}</span>
            </div>
          ))}
        </div>
        <div style={{ background: '#0f1520', border: '1px solid #1e293b', borderRadius: 12, padding: '1.25rem' }}>
          <div style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.75rem' }}>Positive Factors</div>
          {detail.risk_profile.positive_factors?.map((f: string) => (
            <div key={f} style={{ fontSize: 12, color: '#22c55e', marginBottom: 6, display: 'flex', gap: 8 }}>
              <span>✓</span><span>{f}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      {!decision && (
        <div style={{ display: 'flex', gap: 12 }}>
          <button
            onClick={() => setDecision('approved')}
            style={{
              flex: 1,
              padding: '14px',
              background: '#22c55e',
              color: '#080c10',
              border: 'none',
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 700,
              cursor: 'pointer',
              fontFamily: 'monospace'
            }}>
            ✓ Approve — ₹{(rec.suggested_amount / 100000).toFixed(0)}L at {rec.suggested_rate}%
          </button>
          <button
            onClick={() => setShowReject(true)}
            style={{
              padding: '14px 24px',
              background: 'transparent',
              color: '#ef4444',
              border: '1px solid #ef4444',
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 600,
              cursor: 'pointer',
              fontFamily: 'monospace'
            }}>
            Reject
          </button>
          <button
            onClick={() => setDecision('more_info')}
            style={{
              padding: '14px 24px',
              background: 'transparent',
              color: '#f59e0b',
              border: '1px solid #f59e0b',
              borderRadius: 8,
              fontSize: 14,
              cursor: 'pointer',
              fontFamily: 'monospace'
            }}>
            Request Info
          </button>
        </div>
      )}

      {/* Decision Result */}
      {decision && (
        <div style={{
          padding: '1.5rem',
          background: decision === 'approved' ? 'rgba(34,197,94,0.1)' : decision === 'rejected' ? 'rgba(239,68,68,0.1)' : 'rgba(245,158,11,0.1)',
          border: `1px solid ${decision === 'approved' ? '#22c55e' : decision === 'rejected' ? '#ef4444' : '#f59e0b'}40`,
          borderRadius: 10,
          textAlign: 'center',
          color: decision === 'approved' ? '#22c55e' : decision === 'rejected' ? '#ef4444' : '#f59e0b',
          fontFamily: 'monospace',
          fontSize: 16,
          fontWeight: 600
        }}>
          {decision === 'approved' && '✓ Approved — CreditBridge will notify the business'}
          {decision === 'rejected' && '✗ Rejected — Logged for model improvement'}
          {decision === 'more_info' && '? More info requested — Business will be notified'}
        </div>
      )}

      {/* Rejection Modal */}
      {showReject && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100
        }}>
          <div style={{ background: '#0f1520', border: '1px solid #1e293b', borderRadius: 12, padding: '1.5rem', width: 420 }}>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#f1f5f9', marginBottom: '1rem' }}>Rejection Reason</div>
            <select
              value={rejectionReason}
              onChange={e => setRejectionReason(e.target.value)}
              style={{
                width: '100%', padding: '10px 12px',
                background: '#080c10', border: '1px solid #1e293b',
                borderRadius: 8, color: '#e2e8f0', fontSize: 13,
                marginBottom: '1rem', outline: 'none'
              }}>
              <option value="">Select reason...</option>
              <option value="score_too_low">Score too low</option>
              <option value="gst_mismatch">GST mismatch</option>
              <option value="low_vintage">Insufficient vintage</option>
              <option value="low_turnover">Low turnover</option>
              <option value="high_bounce">High bounce rate</option>
              <option value="sector_risk">Sector risk</option>
              <option value="incomplete_data">Incomplete data</option>
              <option value="internal_policy">Internal policy</option>
            </select>
            <div style={{ display: 'flex', gap: 10 }}>
              <button onClick={handleReject} disabled={!rejectionReason}
                style={{ flex: 1, padding: '10px', background: '#ef4444', color: '#fff', border: 'none', borderRadius: 8, fontSize: 13, cursor: 'pointer', fontFamily: 'monospace' }}>
                Confirm Reject
              </button>
              <button onClick={() => setShowReject(false)}
                style={{ padding: '10px 16px', background: 'transparent', color: '#64748b', border: '1px solid #1e293b', borderRadius: 8, fontSize: 13, cursor: 'pointer' }}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}