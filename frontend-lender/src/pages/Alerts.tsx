import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { getPool } from '../api/lender'

// ─── Types ────────────────────────────────────────────────────────
interface Alert {
  id: string
  business_id: string
  business_name: string
  city: string
  score: number
  grade: string
  type: string
  severity: 'critical' | 'warning' | 'info' | 'positive'
  message: string
  action: string
  timestamp: string
  acknowledged: boolean
}

interface PortfolioStats {
  total_alerts: number
  critical: number
  warning: number
  info: number
  positive: number
}

// ─── Mock alert generator from pool data ──────────────────────────
function generateAlerts(pool: any[]): Alert[] {
  const alerts: Alert[] = []
  const now = new Date()

  pool.forEach((biz, i) => {
    const flags = biz.flags || []
    const score = biz.score || 0

    // Score based alerts
    if (score < 650) {
      alerts.push({
        id: `alert-critical-${biz.business_id}`,
        business_id: biz.business_id,
        business_name: biz.business_name,
        city: biz.city,
        score,
        grade: biz.grade,
        type: 'low_score',
        severity: 'critical',
        message: `Score ${score} — below safe threshold of 650. Immediate review needed.`,
        action: 'Review loan exposure',
        timestamp: new Date(now.getTime() - i * 3600000).toISOString(),
        acknowledged: false
      })
    } else if (score < 700) {
      alerts.push({
        id: `alert-warn-score-${biz.business_id}`,
        business_id: biz.business_id,
        business_name: biz.business_name,
        city: biz.city,
        score,
        grade: biz.grade,
        type: 'score_declining',
        severity: 'warning',
        message: `Score ${score} approaching review threshold. Monitor monthly.`,
        action: 'Monitor closely',
        timestamp: new Date(now.getTime() - i * 7200000).toISOString(),
        acknowledged: false
      })
    }

    // Flag based alerts
    if (flags.includes('high_bounce_rate')) {
      alerts.push({
        id: `alert-bounce-${biz.business_id}`,
        business_id: biz.business_id,
        business_name: biz.business_name,
        city: biz.city,
        score,
        grade: biz.grade,
        type: 'bounce_detected',
        severity: 'critical',
        message: `High bounce rate detected — payment discipline deteriorating.`,
        action: 'Contact business owner immediately',
        timestamp: new Date(now.getTime() - i * 1800000).toISOString(),
        acknowledged: false
      })
    }

    if (flags.includes('gst_bank_mismatch')) {
      alerts.push({
        id: `alert-gst-${biz.business_id}`,
        business_id: biz.business_id,
        business_name: biz.business_name,
        city: biz.city,
        score,
        grade: biz.grade,
        type: 'gst_mismatch',
        severity: 'warning',
        message: `GST declared revenue doesn't match bank credits. Possible under-reporting.`,
        action: 'Request GST reconciliation',
        timestamp: new Date(now.getTime() - i * 5400000).toISOString(),
        acknowledged: false
      })
    }

    if (flags.includes('customer_concentration_risk')) {
      alerts.push({
        id: `alert-conc-${biz.business_id}`,
        business_id: biz.business_id,
        business_name: biz.business_name,
        city: biz.city,
        score,
        grade: biz.grade,
        type: 'concentration_risk',
        severity: 'warning',
        message: `Top 3 customers represent 70%+ of revenue. Single buyer risk.`,
        action: 'Note in loan file',
        timestamp: new Date(now.getTime() - i * 9000000).toISOString(),
        acknowledged: false
      })
    }

    // Positive alerts for good performers
    if (score >= 800) {
      alerts.push({
        id: `alert-positive-${biz.business_id}`,
        business_id: biz.business_id,
        business_name: biz.business_name,
        city: biz.city,
        score,
        grade: biz.grade,
        type: 'excellent_performance',
        severity: 'positive',
        message: `Score ${score} (${biz.grade}) — excellent performance. Pre-approval recommended.`,
        action: 'Consider pre-approved offer',
        timestamp: new Date(now.getTime() - i * 12000000).toISOString(),
        acknowledged: false
      })
    }
  })

  return alerts.sort((a, b) => {
    const order = { critical: 0, warning: 1, info: 2, positive: 3 }
    return order[a.severity] - order[b.severity]
  })
}

// ─── Severity config ──────────────────────────────────────────────
const SEV = {
  critical: { color: '#ef4444', bg: 'rgba(239,68,68,0.08)', border: 'rgba(239,68,68,0.25)', icon: '🔴', label: 'Critical' },
  warning:  { color: '#f59e0b', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.25)', icon: '🟡', label: 'Warning' },
  info:     { color: '#4a9eff', bg: 'rgba(74,158,255,0.08)', border: 'rgba(74,158,255,0.25)', icon: '🔵', label: 'Info' },
  positive: { color: '#22c55e', bg: 'rgba(34,197,94,0.08)',  border: 'rgba(34,197,94,0.25)',  icon: '🟢', label: 'Positive' },
}

const TYPE_LABELS: Record<string, string> = {
  low_score:             'Low Score',
  score_declining:       'Score Declining',
  bounce_detected:       'Bounce Detected',
  gst_mismatch:          'GST Mismatch',
  concentration_risk:    'Concentration Risk',
  revenue_drop:          'Revenue Drop',
  overdue_invoices:      'Overdue Invoices',
  excellent_performance: 'Excellent Performance',
}

// ─── Alert Card ───────────────────────────────────────────────────
function AlertCard({
  alert,
  onAcknowledge,
  onViewBusiness,
}: {
  alert: Alert
  onAcknowledge: (id: string) => void
  onViewBusiness: (id: string) => void
}) {
  const sev = SEV[alert.severity]
  const timeAgo = (() => {
    const diff = Date.now() - new Date(alert.timestamp).getTime()
    const mins = Math.floor(diff / 60000)
    const hrs = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)
    if (days > 0) return `${days}d ago`
    if (hrs > 0) return `${hrs}h ago`
    return `${mins}m ago`
  })()

  return (
    <div style={{
      background: alert.acknowledged ? '#0a0a0f' : sev.bg,
      border: `1px solid ${alert.acknowledged ? '#1e293b' : sev.border}`,
      borderLeft: `3px solid ${alert.acknowledged ? '#1e293b' : sev.color}`,
      borderRadius: 10,
      padding: '1rem 1.25rem',
      opacity: alert.acknowledged ? 0.5 : 1,
      transition: 'all 0.2s'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>

        {/* Left */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 14 }}>{sev.icon}</span>
            <span style={{
              fontSize: 10, padding: '2px 8px', borderRadius: 12,
              background: sev.bg, color: sev.color,
              border: `0.5px solid ${sev.border}`, fontWeight: 600,
              textTransform: 'uppercase', letterSpacing: '0.06em'
            }}>
              {TYPE_LABELS[alert.type] || alert.type}
            </span>
            <span style={{ fontSize: 11, color: '#64748b', fontFamily: 'monospace' }}>{timeAgo}</span>
            {alert.acknowledged && (
              <span style={{ fontSize: 10, color: '#475569', padding: '2px 8px', borderRadius: 12, background: '#1e293b' }}>
                Acknowledged
              </span>
            )}
          </div>

          {/* Business */}
          <div style={{ fontSize: 14, fontWeight: 600, color: '#f1f5f9', marginBottom: 4 }}>
            {alert.business_name}
            <span style={{ fontSize: 11, color: '#64748b', fontWeight: 400, marginLeft: 8 }}>
              {alert.city} · Score {alert.score} ({alert.grade})
            </span>
          </div>

          {/* Message */}
          <div style={{ fontSize: 13, color: '#94a3b8', lineHeight: 1.5, marginBottom: 8 }}>
            {alert.message}
          </div>

          {/* Action */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Action:</span>
            <span style={{ fontSize: 12, color: sev.color, fontWeight: 500 }}>{alert.action}</span>
          </div>
        </div>

        {/* Right — buttons */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, flexShrink: 0 }}>
          <button
            onClick={() => onViewBusiness(alert.business_id)}
            style={{
              padding: '6px 14px', background: 'transparent',
              border: '1px solid #4a9eff', borderRadius: 6,
              color: '#4a9eff', fontSize: 11, cursor: 'pointer',
              fontFamily: 'monospace', whiteSpace: 'nowrap'
            }}>
            View →
          </button>
          {!alert.acknowledged && (
            <button
              onClick={() => onAcknowledge(alert.id)}
              style={{
                padding: '6px 14px', background: 'transparent',
                border: '1px solid #1e293b', borderRadius: 6,
                color: '#64748b', fontSize: 11, cursor: 'pointer',
                fontFamily: 'monospace', whiteSpace: 'nowrap'
              }}>
              ✓ Done
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Main Component ───────────────────────────────────────────────
export default function Alerts() {
  const navigate = useNavigate()
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'critical' | 'warning' | 'positive'>('all')
  const [showAcknowledged, setShowAcknowledged] = useState(false)
  const [lastRefresh, setLastRefresh] = useState(new Date())

  const loadAlerts = useCallback(async () => {
    try {
      const res = await getPool({})
      const pool = res.data?.pool || []
      const generated = generateAlerts(pool)
      setAlerts(prev => {
        // Preserve acknowledged state
        const ackMap = new Map(prev.map(a => [a.id, a.acknowledged]))
        return generated.map(a => ({ ...a, acknowledged: ackMap.get(a.id) ?? false }))
      })
      setLastRefresh(new Date())
    } catch {
      // Keep existing
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAlerts()
    const interval = setInterval(loadAlerts, 60000) // Refresh every 60s
    return () => clearInterval(interval)
  }, [loadAlerts])

  const handleAcknowledge = (id: string) => {
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, acknowledged: true } : a))
  }

  const acknowledgeAll = () => {
    setAlerts(prev => prev.map(a => ({ ...a, acknowledged: true })))
  }

  // Stats
  const active = alerts.filter(a => !a.acknowledged)
  const stats: PortfolioStats = {
    total_alerts: active.length,
    critical: active.filter(a => a.severity === 'critical').length,
    warning: active.filter(a => a.severity === 'warning').length,
    info: active.filter(a => a.severity === 'info').length,
    positive: active.filter(a => a.severity === 'positive').length,
  }

  const filtered = alerts.filter(a => {
    if (!showAcknowledged && a.acknowledged) return false
    if (filter !== 'all' && a.severity !== filter) return false
    return true
  })

  return (
    <div style={{ minHeight: '100vh', background: '#080c10', padding: '1.5rem' }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', paddingBottom: '1rem', borderBottom: '1px solid #1e293b' }}>
        <div>
          <div style={{ fontSize: 11, color: '#4a9eff', letterSpacing: '0.15em', textTransform: 'uppercase', fontFamily: 'monospace' }}>
            CreditBridge
          </div>
          <div style={{ fontSize: 20, fontWeight: 600, color: '#f1f5f9', marginTop: 4 }}>
            Portfolio Alerts
          </div>
          <div style={{ fontSize: 11, color: '#475569', marginTop: 2, fontFamily: 'monospace' }}>
            Last refresh: {lastRefresh.toLocaleTimeString()} · Auto-refreshes every 60s
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={loadAlerts}
            style={{ padding: '8px 14px', background: 'transparent', border: '1px solid #1e293b', borderRadius: 6, color: '#64748b', fontSize: 12, cursor: 'pointer', fontFamily: 'monospace' }}>
            ↻ Refresh
          </button>
          <button
            onClick={() => navigate('/pool')}
            style={{ padding: '8px 14px', background: 'transparent', border: '1px solid #1e293b', borderRadius: 6, color: '#94a3b8', fontSize: 12, cursor: 'pointer', fontFamily: 'monospace' }}>
            Pool →
          </button>
          <button
            onClick={() => navigate('/portfolio')}
            style={{ padding: '8px 14px', background: 'transparent', border: '1px solid #1e293b', borderRadius: 6, color: '#94a3b8', fontSize: 12, cursor: 'pointer', fontFamily: 'monospace' }}>
            Portfolio →
          </button>
        </div>
      </div>

      {/* Stats Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 10, marginBottom: '1.5rem' }}>
        {[
          { label: 'Total Active', value: stats.total_alerts, color: '#f1f5f9' },
          { label: 'Critical', value: stats.critical, color: '#ef4444' },
          { label: 'Warning', value: stats.warning, color: '#f59e0b' },
          { label: 'Info', value: stats.info, color: '#4a9eff' },
          { label: 'Positive', value: stats.positive, color: '#22c55e' },
        ].map(s => (
          <div key={s.label} style={{ background: '#0f1520', border: '1px solid #1e293b', borderRadius: 10, padding: '0.875rem 1rem' }}>
            <div style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>
              {s.label}
            </div>
            <div style={{ fontSize: 28, fontWeight: 700, color: s.color, fontFamily: 'monospace', lineHeight: 1 }}>
              {s.value}
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: 8 }}>
        <div style={{ display: 'flex', gap: 6 }}>
          {(['all', 'critical', 'warning', 'positive'] as const).map(f => {
            const isActive = filter === f
            const color = f === 'critical' ? '#ef4444' : f === 'warning' ? '#f59e0b' : f === 'positive' ? '#22c55e' : '#4a9eff'
            return (
              <button key={f} onClick={() => setFilter(f)}
                style={{
                  padding: '6px 14px',
                  background: isActive ? `${color}15` : 'transparent',
                  border: `1px solid ${isActive ? color : '#1e293b'}`,
                  borderRadius: 20, color: isActive ? color : '#64748b',
                  fontSize: 12, cursor: 'pointer', fontFamily: 'monospace',
                  fontWeight: isActive ? 600 : 400, textTransform: 'capitalize'
                }}>
                {f === 'all' ? `All (${stats.total_alerts})` : f}
              </button>
            )
          })}
        </div>

        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', fontSize: 12, color: '#64748b' }}>
            <input
              type="checkbox"
              checked={showAcknowledged}
              onChange={e => setShowAcknowledged(e.target.checked)}
              style={{ cursor: 'pointer' }}
            />
            Show acknowledged
          </label>
          {active.length > 0 && (
            <button
              onClick={acknowledgeAll}
              style={{ padding: '6px 14px', background: 'transparent', border: '1px solid #1e293b', borderRadius: 6, color: '#64748b', fontSize: 12, cursor: 'pointer' }}>
              Acknowledge all
            </button>
          )}
        </div>
      </div>

      {/* Alert List */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b', fontFamily: 'monospace' }}>
          Loading alerts...
        </div>
      ) : filtered.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '4rem', background: '#0f1520', borderRadius: 12, border: '1px solid #1e293b' }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>
            {stats.total_alerts === 0 ? '✅' : '🔍'}
          </div>
          <div style={{ fontSize: 16, color: '#94a3b8', fontWeight: 500, marginBottom: 6 }}>
            {stats.total_alerts === 0
              ? 'Portfolio clean — no active alerts'
              : 'No alerts match current filter'}
          </div>
          <div style={{ fontSize: 12, color: '#475569' }}>
            {stats.total_alerts === 0
              ? 'All businesses in your pool are performing well'
              : 'Try changing the filter above'}
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {filtered.map(alert => (
            <AlertCard
              key={alert.id}
              alert={alert}
              onAcknowledge={handleAcknowledge}
              onViewBusiness={(id) => navigate(`/business/${id}`)}
            />
          ))}
        </div>
      )}

      {/* Bottom insight */}
      {!loading && stats.critical > 0 && (
        <div style={{ marginTop: '1.5rem', padding: '1rem 1.25rem', background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#ef4444', marginBottom: 3 }}>
              {stats.critical} critical alert{stats.critical > 1 ? 's' : ''} need immediate attention
            </div>
            <div style={{ fontSize: 11, color: '#94a3b8' }}>
              Review these businesses before processing any new loan requests
            </div>
          </div>
          <button
            onClick={() => setFilter('critical')}
            style={{ padding: '8px 16px', background: 'rgba(239,68,68,0.15)', border: '1px solid #ef4444', borderRadius: 6, color: '#ef4444', fontSize: 12, cursor: 'pointer', fontWeight: 600, fontFamily: 'monospace' }}>
            View Critical →
          </button>
        </div>
      )}
    </div>
  )
}