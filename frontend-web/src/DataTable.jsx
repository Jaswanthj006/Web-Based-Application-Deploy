import './DataTable.css'

export function DataTable({ data }) {
  if (!data || data.length === 0) return null
  const cols = Object.keys(data[0]).filter((k) => k && k !== 'undefined')
  return (
    <section className="data-table-section">
      <h2>Data Table</h2>
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              {cols.map((c) => (
                <th key={c}>{c}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => (
              <tr key={i}>
                {cols.map((c) => (
                  <td key={c}>{row[c] ?? ''}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
