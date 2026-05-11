import { useState } from 'react'
import { useApp } from '../../state/AppState.jsx'

const COLUMNS = [
  { id: 'todo',       label: 'To do' },
  { id: 'inprogress', label: 'In progress' },
  { id: 'review',     label: 'Review' },
  { id: 'done',       label: 'Done' },
]

const PRIORITIES = ['Low', 'Medium', 'High', 'Urgent']

export default function Tasks() {
  const { state, activeBrand, addTask, moveTask, deleteTask } = useApp()
  const [draft, setDraft] = useState({ title: '', priority: 'Medium', due: '' })
  const [dragging, setDragging] = useState(null)
  const [dropTarget, setDropTarget] = useState(null)

  const submit = (e) => {
    e.preventDefault()
    if (!draft.title.trim()) return
    addTask({ title: draft.title.trim(), priority: draft.priority.toLowerCase(), due: draft.due || null })
    setDraft({ title: '', priority: 'Medium', due: '' })
  }

  const onDragStart = (id) => (e) => {
    setDragging(id)
    e.dataTransfer?.setData('text/plain', id)
    e.dataTransfer.effectAllowed = 'move'
  }
  const onDragOver = (col) => (e) => {
    e.preventDefault()
    setDropTarget(col)
  }
  const onDrop = (col) => (e) => {
    e.preventDefault()
    const id = dragging || e.dataTransfer?.getData('text/plain')
    if (id) moveTask(id, col)
    setDragging(null)
    setDropTarget(null)
  }

  const priorityColor = (p) => ({
    urgent: 'var(--danger-ink)',
    high:   'var(--accent)',
    medium: 'var(--muted)',
    low:    'var(--muted-2)',
  }[p] || 'var(--muted)')

  return (
    <>
      <h1 className="page-h1">Tasks · <em>{activeBrand?.name}</em></h1>
      <p className="page-sub">Drag cards between columns. Add team mates to assign work.</p>

      <form onSubmit={submit} className="card-tp">
        <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
          <input
            style={{ flex: 1, minWidth: 220 }}
            placeholder="What needs doing?"
            value={draft.title}
            onChange={e => setDraft({ ...draft, title: e.target.value })}
          />
          <select style={{ width: 130 }} value={draft.priority} onChange={e => setDraft({ ...draft, priority: e.target.value })}>
            {PRIORITIES.map(p => <option key={p}>{p}</option>)}
          </select>
          <input type="date" style={{ width: 170 }} value={draft.due} onChange={e => setDraft({ ...draft, due: e.target.value })} />
          <button type="submit" className="btn-tp primary">Add task</button>
          <button type="button" className="btn-tp ghost">Team (1)</button>
        </div>
      </form>

      <div className="kanban">
        {COLUMNS.map(col => {
          const items = state.tasks.filter(t => t.column === col.id)
          return (
            <div
              key={col.id}
              className="kanban-col"
              onDragOver={onDragOver(col.id)}
              onDragLeave={() => setDropTarget(null)}
              onDrop={onDrop(col.id)}
            >
              <h4>{col.label} <span style={{ opacity: .6 }}>· {items.length}</span></h4>
              {items.map(t => (
                <div
                  key={t.id}
                  className={`kanban-card ${dragging === t.id ? 'dragging' : ''}`}
                  draggable
                  onDragStart={onDragStart(t.id)}
                  onDragEnd={() => setDragging(null)}
                >
                  <div style={{ fontSize: 14 }}>{t.title}</div>
                  <div className="row between">
                    <span className="tiny" style={{ color: priorityColor(t.priority), textTransform: 'uppercase', letterSpacing: 1 }}>
                      {t.priority}
                    </span>
                    <button onClick={() => deleteTask(t.id)} className="btn-tp ghost" style={{ padding: '2px 6px', fontSize: 11 }}>×</button>
                  </div>
                </div>
              ))}
              <div className={`kanban-drop ${dropTarget === col.id ? 'active' : ''}`}>Drop here</div>
            </div>
          )
        })}
      </div>
    </>
  )
}
