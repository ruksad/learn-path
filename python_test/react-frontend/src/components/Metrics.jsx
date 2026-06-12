import { useState } from 'react'
import { getMetrics } from '../services/api'
import './Metrics.css'

function Metrics({ metrics, onRefresh }) {
  const [refreshing, setRefreshing] = useState(false)

  const handleRefresh = async () => {
    setRefreshing(true)
    await onRefresh()
    setRefreshing(false)
  }

  if (!metrics) return null

  const { requests, store, uptime_seconds } = metrics
  const times = requests?.response_times_ms || {}

  return (
    <div className="metrics-panel">
      <div className="metrics-header">
        <h3>Backend Metrics</h3>
        <button className="metrics-refresh-btn" onClick={handleRefresh} disabled={refreshing}>
          {refreshing ? '…' : '↻'}
        </button>
      </div>

      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-value">{requests?.total_requests ?? 0}</div>
          <div className="metric-label">Total Requests</div>
        </div>
        <div className="metric-card error">
          <div className="metric-value">{requests?.errors_4xx ?? 0}</div>
          <div className="metric-label">4xx Errors</div>
        </div>
        <div className="metric-card error-5">
          <div className="metric-value">{requests?.errors_5xx ?? 0}</div>
          <div className="metric-label">5xx Errors</div>
        </div>
        <div className="metric-card uptime">
          <div className="metric-value">{uptime_seconds ?? 0}s</div>
          <div className="metric-label">Uptime</div>
        </div>
      </div>

      <div className="metrics-row">
        <div className="metrics-group">
          <h4>Response Times</h4>
          <div className="time-pills">
            <span className="time-pill avg">avg {times.avg ?? 0}ms</span>
            <span className="time-pill min">min {times.min ?? 0}ms</span>
            <span className="time-pill max">max {times.max ?? 0}ms</span>
          </div>
        </div>

        {requests?.by_method && (
          <div className="metrics-group">
            <h4>By Method</h4>
            <div className="bar-list">
              {Object.entries(requests.by_method).map(([method, count]) => (
                <div key={method} className="bar-row">
                  <span className="bar-label">{method}</span>
                  <div className="bar-track">
                    <div
                      className="bar-fill"
                      style={{ width: `${Math.min(100, (count / (requests.total_requests || 1)) * 100)}%` }}
                    />
                  </div>
                  <span className="bar-count">{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {requests?.by_status && (
          <div className="metrics-group">
            <h4>By Status</h4>
            <div className="status-pills">
              {Object.entries(requests.by_status).map(([code, count]) => (
                <span
                  key={code}
                  className={`status-pill status-${Math.floor(parseInt(code) / 100)}xx`}
                >
                  {code}: {count}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Metrics
