import { useState } from 'react'
import { updateTask } from '../services/api'
import './TaskList.css'

const STATUSES = ['pending', 'in-progress', 'completed']

const STATUS_COLORS = {
  completed: '#4caf50',
  'in-progress': '#ff9800',
  pending: '#f44336',
}

function TaskCard({ task, onUpdated }) {
  const [updating, setUpdating] = useState(false)
  const [error, setError] = useState(null)

  const handleStatusChange = async (e) => {
    const newStatus = e.target.value
    if (newStatus === task.status) return
    setUpdating(true)
    setError(null)
    try {
      const updated = await updateTask(task.id, { status: newStatus })
      onUpdated(updated)
    } catch (err) {
      setError(err.message)
    } finally {
      setUpdating(false)
    }
  }

  return (
    <div className={`task-card ${updating ? 'updating' : ''}`}>
      <div className="task-header">
        <h3>{task.title}</h3>
        <span
          className="task-status-badge"
          style={{ backgroundColor: STATUS_COLORS[task.status] || '#9e9e9e' }}
        >
          {task.status}
        </span>
      </div>

      <div className="task-footer">
        <span className="task-id">Task #{task.id}</span>
        <span className="task-user">User #{task.userId}</span>
        <label className="status-select-label">
          <span>Status:</span>
          <select
            value={task.status}
            onChange={handleStatusChange}
            disabled={updating}
            className="status-select"
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          {updating && <span className="updating-indicator">saving…</span>}
        </label>
      </div>

      {error && <p className="task-error">{error}</p>}
    </div>
  )
}

function TaskList({ tasks, onTaskUpdated }) {
  if (tasks.length === 0) {
    return <div className="empty-state">No tasks found</div>
  }

  return (
    <div className="task-list">
      {tasks.map((task) => (
        <TaskCard key={task.id} task={task} onUpdated={onTaskUpdated} />
      ))}
    </div>
  )
}

export default TaskList
