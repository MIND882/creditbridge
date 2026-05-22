import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getPool, getSegments } from '../api/lender'

export default function Pool() {
  const navigate = useNavigate()
  const [pool, setPool] = useState<any[]>([])
  const [segments, setSegments] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    min_score: '',
    city: '',
    business_type: '',
    grade: ''
  })

  const load = async () => {
    setLoading(true)
    try {
      const params: any = {}
      if (filters.min_score) params.min_score = parseInt(filters.min_score)
      if (filters.city) params.city = filters.city
      if (filters.business_type) params.business_type = filters.business_type
      if (filters.grade) params.grade = filters.grade

      const [poolRes, segRes] = await Promise.all([
        getPool(params),
        getSegments()
      ])
      setPool(poolRes.data.pool)
      setSegments(segRes.data)
    } catch (e) {
      navigate('/')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const gradeColor = (g: string) => {
    if (g === 'A+' || g === 'A') return '#22c55e'
    if (g === 'B+' || g === 'B') return '#f59e0b'
    return '#ef4444'
  }

  const inp = {
    background: '#0f1520',
    border: '1px solid #1e293b',
    borderRadius: 6,
    padding: '8px 12px',
    color: '#e2e8f0',
    fontSize: 12,
    fontFamily: 'monospace',
    outline: 'none',
    width: '100%'
  }

  return (
    <div style={{ minHeight: '100vh', background: '#080c10', padding: '1.5rem' }}>

      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1.5rem',
        paddingBottom: '1rem',
        borderBottom: '1px solid #1e293b'
      }}>
        <div>
          <div style={{ fontSize: 11, color: '#4a9eff', letterSpacing: '0.15em', textTransform: 'uppercase', fontFamily: 'monospace' }}>
            CreditBridge
          </div>
          <div style={{ fontSize: 20, fontWeight: 600, color: '#f1f5f9', marginTop: 4 }}>
            MSME Credit Pool
          </div>
        </div>
        <button
          onClick={() => { localStorage.removeItem('lender_api_key'); navigate('/') }}
          style={{ fontSize: 11, color: '#64748b', background: 'transparent', border: 'none', cursor: 'pointer', fontFamily: 'monospace' }}>
          Sign out
        </button>
      </div>

      {/* Segments */}
      {segments && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: '1.5rem' }}>
          {[
            ['Total Businesses', segments.total_businesses, '#4a9eff'],
            ['Deployable Capital', `₹${(segments.total_deployable_capital / 10000000).toFixed(1)}Cr`, '#22c55e'],
            ['Pool Quality', segments.recommendation?.split('%')[0] + '%' || 'N/A', '#f59e0b'],
            ['A+ Grade', segments.segments?.find((s: any) => s.grade === 'A+')?.count || 0, '#22c55e'],
          ].map(([label, val, color]) => (
            <div key={String(label)} style={{
              background: '#0f1520',
              border: '1px solid #1e293b',
              borderRadius: 10,
              padding: '1rem'
            }}>
              <div style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>
                {label}
              </div>
              <div style={{ fontSize: 22, fontWeight: 600, color: color as string, fontFamily: 'monospace' }}>
                {val}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 10,
        marginBottom: '1rem',
        padding: '1rem',
        background: '#0f1520',
        borderRadius: 10,
        border: '1px solid #1e293b'
      }}>
        {[
          ['Min Score', 'min_score', '700'],
          ['City', 'city', 'Surat'],
          ['Business Type', 'business_type', 'textile'],
          ['Grade', 'grade', 'A+'],
        ].map(([label, key, ph]) => (
          <div key={key as string}>
            <div style={{ fontSize: 10, color: '#64748b', marginBottom: 4, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
              {label}
            </div>
            <input
              style={inp}
              placeholder={ph as string}
              value={(filters as any)[key as string]}
              onChange={e => setFilters({ ...filters, [key as string]: e.target.value })}
            />
          </div>
        ))}
      </div>

      <button
        onClick={load}
        style={{
          marginBottom: '1.5rem',
          padding: '8px 20px',
          background: '#4a9eff',
          color: '#080c10',
          border: 'none',
          borderRadius: 6,
          fontSize: 12,
          fontWeight: 600,
          cursor: 'pointer',
          fontFamily: 'monospace'
        }}>
        Apply Filters
      </button>

      {/* Pool Table */}
      {loading ? (
        <div style={{ color: '#64748b', fontFamily: 'monospace', fontSize: 13 }}>Loading pool...</div>
      ) : (
        <div style={{
          background: '#0f1520',
          border: '1px solid #1e293b',
          borderRadius: 10,
          overflow: 'hidden'
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #1e293b' }}>
                {['Business', 'City', 'Score', 'Grade', 'Limit', 'GST Score', 'Confidence', 'Action'].map(h => (
                  <th key={h} style={{
                    padding: '10px 16px',
                    textAlign: 'left',
                    fontSize: 10,
                    color: '#64748b',
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    fontWeight: 500
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {pool.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ padding: '2rem', textAlign: 'center', color: '#64748b', fontSize: 13 }}>
                    No businesses match filters
                  </td>
                </tr>
              ) : pool.map((b, i) => (
                <tr
                  key={b.business_id}
                  style={{
                    borderBottom: i < pool.length - 1 ? '1px solid #1e293b' : 'none',
                    cursor: 'pointer',
                    transition: 'background 0.15s'
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = '#111827')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                >
                  <td style={{ padding: '12px 16px' }}>
                    <div style={{ fontSize: 13, color: '#f1f5f9', fontWeight: 500 }}>{b.business_name}</div>
                    <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>{b.business_type}</div>
                  </td>
                  <td style={{ padding: '12px 16px', fontSize: 12, color: '#94a3b8' }}>{b.city}</td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{
                      fontSize: 15,
                      fontWeight: 700,
                      color: gradeColor(b.grade),
                      fontFamily: 'monospace'
                    }}>{b.score}</span>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{
                      fontSize: 11,
                      padding: '3px 8px',
                      borderRadius: 4,
                      background: `${gradeColor(b.grade)}20`,
                      color: gradeColor(b.grade),
                      fontFamily: 'monospace',
                      fontWeight: 600
                    }}>{b.grade}</span>
                  </td>
                  <td style={{ padding: '12px 16px', fontSize: 13, color: '#22c55e', fontFamily: 'monospace' }}>
                    ₹{(b.recommended_limit / 100000).toFixed(0)}L
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <div style={{ flex: 1, height: 3, background: '#1e293b', borderRadius: 2 }}>
                        <div style={{ width: `${b.gst_compliance_score}%`, height: '100%', background: '#4a9eff', borderRadius: 2 }} />
                      </div>
                      <span style={{ fontSize: 11, color: '#64748b', fontFamily: 'monospace' }}>{b.gst_compliance_score}</span>
                    </div>
                  </td>
                  <td style={{ padding: '12px 16px', fontSize: 12, color: '#94a3b8', fontFamily: 'monospace' }}>
                    {(b.confidence * 100).toFixed(0)}%
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <button
                      onClick={() => navigate(`/business/${b.business_id}`)}
                      style={{
                        padding: '6px 14px',
                        background: 'transparent',
                        border: '1px solid #4a9eff',
                        borderRadius: 6,
                        color: '#4a9eff',
                        fontSize: 11,
                        cursor: 'pointer',
                        fontFamily: 'monospace'
                      }}>
                      Review →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
