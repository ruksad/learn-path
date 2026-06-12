import { useState } from 'react'
import { createTask } from '../services/api'
import './CreateTaskForm.css'

const STATUSES = ['pending', 'in-progress', 'completed']

function CreateTaskForm({ users, onCreated }) {
  const [fields, setFields] = useState({
    title: '',
    status: 'pending',
    userId: users[0]?.id ?? '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [open, setOpen] = useState(false)

  const handleChange = (e) => {
    setFields((prev) => ({ ...prev, [e.target.name]: e.target.value }))
    setError(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const task = await createTask({
        title: fields.title,
        status: fields.status,
        userId: parseInt(fields.userId, 10),
      })
      setFields({ title: '', status: 'pending', userId: users[0]?.id ?? '' })
      setOpen(false)
      onCreated(task)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="create-form-wrapper">
      <button className="toggle-form-btn" onClick={() => setOpen((o) => !o)}>
        {open ? '− Cancel' : '+ Add Task'}
      </button>

      {open && (
        <form className="create-form" onSubmit={handleSubmit}>
          <h4>New Task</h4>

          <label>
            Title
            <input
              name="title"
              value={fields.title}
              onChange={handleChange}
              placeholder="Task description"
              required
            />
          </label>

          <label>
            Status
            <select name="status" value={fields.status} onChange={handleChange}>
              {STATUSES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </label>

          <label>
            Assign to user
            <select name="userId" value={fields.userId} onChange={handleChange}>
              {users.map((u) => (
                <option key={u.id} value={u.id}>{u.name} ({u.role})</option>
              ))}
            </select>
          </label>

          {error && <p className="form-error">{error}</p>}

          <button type="submit" disabled={loading || !users.length} className="submit-btn">
            {loading ? 'Creating…' : 'Create Task'}
          </button>
        </form>
      )}
    </div>
  )
}

export default CreateTaskForm
