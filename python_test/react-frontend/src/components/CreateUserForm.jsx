import { useState } from 'react'
import { createUser } from '../services/api'
import './CreateUserForm.css'

const ROLES = ['developer', 'designer', 'manager', 'admin', 'qa']

function CreateUserForm({ onCreated }) {
  const [fields, setFields] = useState({ name: '', email: '', role: 'developer' })
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
      const user = await createUser(fields)
      setFields({ name: '', email: '', role: 'developer' })
      setOpen(false)
      onCreated(user)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="create-form-wrapper">
      <button className="toggle-form-btn" onClick={() => setOpen((o) => !o)}>
        {open ? '− Cancel' : '+ Add User'}
      </button>

      {open && (
        <form className="create-form" onSubmit={handleSubmit}>
          <h4>New User</h4>

          <label>
            Name
            <input
              name="name"
              value={fields.name}
              onChange={handleChange}
              placeholder="Full name"
              required
            />
          </label>

          <label>
            Email
            <input
              name="email"
              type="email"
              value={fields.email}
              onChange={handleChange}
              placeholder="user@example.com"
              required
            />
          </label>

          <label>
            Role
            <select name="role" value={fields.role} onChange={handleChange}>
              {ROLES.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </label>

          {error && <p className="form-error">{error}</p>}

          <button type="submit" disabled={loading} className="submit-btn">
            {loading ? 'Creating…' : 'Create User'}
          </button>
        </form>
      )}
    </div>
  )
}

export default CreateUserForm
