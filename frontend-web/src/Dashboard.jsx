import { useState, useEffect, useCallback } from 'react'
import { api } from './api'
import { DataTable } from './DataTable'
import { Charts } from './Charts'
import './Dashboard.css'

export function Dashboard({ user, onLogout }) {
  const [history, setHistory] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [summary, setSummary] = useState(null)
  const [data, setData] = useState([])
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [loading, setLoading] = useState(false)

  const loadHistory = useCallback(async () => {
    try {
      const list = await api.history()
      setHistory(list)
      if (list.length && !selectedId) setSelectedId(list[0].id)
    } catch (e) {
      console.error(e)
    }
  }, [selectedId])

  useEffect(() => {
    loadHistory()
  }, [loadHistory])

  useEffect(() => {
    if (!selectedId) {
      setSummary(null)
      setData([])
      return
    }
    setLoading(true)
    Promise.all([api.summary(selectedId), api.data(selectedId)])
      .then(([s, d]) => {
        setSummary(s)
        setData(d.data || [])
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [selectedId])

  const handleUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploadError('')
    setUploading(true)
    try {
      const result = await api.upload(file, file.name)
      await loadHistory()
      setSelectedId(result.id)
    } catch (err) {
      setUploadError(err.message || 'Upload failed')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const downloadPdf = () => {
    if (!selectedId) return
    window.open(api.reportPdfUrl(selectedId), '_blank')
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Chemical Equipment Parameter Visualizer</h1>
        <div className="header-actions">
          <label className="btn btn-primary">
            {uploading ? 'Uploading...' : 'Upload CSV'}
            <input type="file" accept=".csv" onChange={handleUpload} disabled={uploading} hidden />
          </label>
          {selectedId && (
            <a href={api.reportPdfUrl(selectedId)} target="_blank" rel="noreferrer" className="btn btn-secondary">
              Download PDF Report
            </a>
          )}
          <span className="user">{user}</span>
          <button type="button" className="btn btn-outline" onClick={onLogout}>Log out</button>
        </div>
      </header>
      {uploadError && <p className="upload-error">{uploadError}</p>}
      <div className="dashboard-content">
        <aside className="history-panel">
          <h2>History (last 5)</h2>
          <ul>
            {history.map((h) => (
              <li key={h.id}>
                <button
                  className={selectedId === h.id ? 'active' : ''}
                  onClick={() => setSelectedId(h.id)}
                >
                  {h.name || `Dataset ${h.id}`}
                  <span className="count">{h.total_count} items</span>
                </button>
              </li>
            ))}
            {history.length === 0 && <li className="empty">No uploads yet. Upload a CSV above.</li>}
          </ul>
        </aside>
        <main className="main-panel">
          {loading && <p className="loading">Loading...</p>}
          {!loading && summary && (
            <>
              <section className="summary-cards">
                <div className="card">
                  <span className="label">Total count</span>
                  <span className="value">{summary.total_count}</span>
                </div>
                {summary.summary?.averages && Object.entries(summary.summary.averages).map(([k, v]) => (
                  v != null && (
                    <div key={k} className="card">
                      <span className="label">Avg {k}</span>
                      <span className="value">{v}</span>
                    </div>
                  )
                ))}
              </section>
              <Charts summary={summary.summary} data={data} />
              <DataTable data={data} />
            </>
          )}
          {!loading && !summary && selectedId && <p>No data for this dataset.</p>}
          {!loading && !selectedId && history.length === 0 && (
            <p className="hint">Upload a CSV file to get started. You can use the sample file <code>sample_equipment_data.csv</code>.</p>
          )}
        </main>
      </div>
    </div>
  )
}
