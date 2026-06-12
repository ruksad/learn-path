import './HealthStatus.css'

function HealthStatus({ health }) {
  if (!health) {
    return (
      <div className="health-status unknown">
        <span className="status-indicator">⏳</span>
        <span>Checking backend status…</span>
      </div>
    )
  }

  const isHealthy = health.status === 'ok'
  // goBackend is the Python health response forwarded by Node
  const py = health.goBackend

  return (
    <div className={`health-status ${isHealthy ? 'healthy' : 'unhealthy'}`}>
      <div className="health-main">
        <span className="status-indicator">{isHealthy ? '✅' : '❌'}</span>
        <span>{health.message}</span>
      </div>

      {py && (
        <div className="health-details">
          <span className="health-pill">Python {py.status}</span>
          {py.uptime_seconds != null && (
            <span className="health-pill">
              Uptime {py.uptime_seconds}s
            </span>
          )}
          {py.store_users != null && (
            <span className="health-pill">👥 {py.store_users} users</span>
          )}
          {py.store_tasks != null && (
            <span className="health-pill">📋 {py.store_tasks} tasks</span>
          )}
        </div>
      )}
    </div>
  )
}

export default HealthStatus
