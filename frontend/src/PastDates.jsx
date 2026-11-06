import { formatDate } from './attendanceState'

export default function PastDates({ dates, selected, onPick }) {
  return (
    <section className="card">
      <h2>Past dates</h2>
      {dates.length === 0 ? (
        <p className="muted">No attendance saved yet.</p>
      ) : (
        <ul className="date-list">
          {dates.map((d) => (
            <li key={d}>
              <button
                className={d === selected ? 'selected' : ''}
                aria-current={d === selected ? 'date' : undefined}
                onClick={() => onPick(d)}
              >
                {formatDate(d)}
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
