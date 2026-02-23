import React, { useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '')
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin123')
  const [config, setConfig] = useState(null)
  const [deals, setDeals] = useState([])
  const [runs, setRuns] = useState([])

  const authHeaders = useMemo(() => ({ Authorization: `Bearer ${token}` }), [token])

  async function login(e) {
    e.preventDefault()
    const fd = new FormData()
    fd.append('username', username)
    fd.append('password', password)
    const r = await fetch(`${API}/auth/login`, { method: 'POST', body: fd })
    const data = await r.json()
    if (data.access_token) {
      setToken(data.access_token)
      localStorage.setItem('token', data.access_token)
      await loadAll(data.access_token)
    } else alert('Falha no login')
  }

  async function loadAll(currentToken = token) {
    const headers = { Authorization: `Bearer ${currentToken}` }
    const [c, d, r] = await Promise.all([
      fetch(`${API}/config`, { headers }),
      fetch(`${API}/deals`, { headers }),
      fetch(`${API}/runs`, { headers }),
    ])
    setConfig(await c.json())
    setDeals(await d.json())
    setRuns(await r.json())
  }

  async function saveConfig() {
    await fetch(`${API}/config`, {
      method: 'PUT',
      headers: { ...authHeaders, 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    })
    await loadAll()
  }

  async function runScan() {
    await fetch(`${API}/scan/run`, { method: 'POST', headers: authHeaders })
    await loadAll()
  }

  async function approve(id) {
    await fetch(`${API}/deals/${id}/approve`, { method: 'POST', headers: authHeaders })
    await loadAll()
  }

  async function reject(id) {
    await fetch(`${API}/deals/${id}/reject`, { method: 'POST', headers: authHeaders })
    await loadAll()
  }

  if (!token) {
    return <div style={{ padding: 20 }}><h2>SmartDeals Login</h2><form onSubmit={login}><input value={username} onChange={e => setUsername(e.target.value)} /><input type="password" value={password} onChange={e => setPassword(e.target.value)} /><button>Entrar</button></form></div>
  }

  return (
    <div style={{ fontFamily: 'Arial', padding: 16 }}>
      <h1>SmartDeals Dashboard</h1>
      <button onClick={() => loadAll()}>Atualizar</button>
      <button onClick={runScan}>Rodar Scan Agora</button>

      {config && (
        <section>
          <h2>Configuração</h2>
          <label>Modo: </label>
          <select value={config.mode} onChange={e => setConfig({ ...config, mode: e.target.value })}>
            <option>MANUAL</option><option>AUTO</option>
          </select>
          <label>Threshold: </label>
          <input type="number" value={config.approval_threshold} onChange={e => setConfig({ ...config, approval_threshold: Number(e.target.value) })} />
          <label>Keywords (linha por linha): </label>
          <textarea value={config.seed_keywords.join('\n')} onChange={e => setConfig({ ...config, seed_keywords: e.target.value.split('\n').map(v => v.trim()).filter(Boolean) })} rows={4} cols={40} />
          <label>Amazon links (linha por linha): </label>
          <textarea value={(config.amazon?.manual_links || []).join('\n')} onChange={e => setConfig({ ...config, amazon: { ...config.amazon, manual_links: e.target.value.split('\n').map(v => v.trim()).filter(Boolean) } })} rows={4} cols={40} />
          <label>Telegram Bot Token: </label>
          <input value={config.telegram.bot_token} onChange={e => setConfig({ ...config, telegram: { ...config.telegram, bot_token: e.target.value } })} />
          <label>Telegram Chat ID: </label>
          <input value={config.telegram.chat_id} onChange={e => setConfig({ ...config, telegram: { ...config.telegram, chat_id: e.target.value } })} />
          <label>WhatsApp provider: </label>
          <select value={config.whatsapp.provider} onChange={e => setConfig({ ...config, whatsapp: { ...config.whatsapp, provider: e.target.value } })}><option value="draft">draft</option><option value="cloud_api">cloud_api</option></select>
          <div><button onClick={saveConfig}>Salvar Config</button></div>
        </section>
      )}

      <section>
        <h2>Deals</h2>
        <table border="1" cellPadding="6">
          <thead><tr><th>ID</th><th>Fonte</th><th>Título</th><th>Preço</th><th>Score</th><th>Status</th><th>Ações</th></tr></thead>
          <tbody>
            {deals.map(d => <tr key={d.id}><td>{d.id}</td><td>{d.source}</td><td>{d.title}</td><td>{d.current_price}</td><td>{d.score}</td><td>{d.status}</td><td><button onClick={() => approve(d.id)}>Aprovar+Postar</button><button onClick={() => reject(d.id)}>Rejeitar</button></td></tr>)}
          </tbody>
        </table>
      </section>

      <section>
        <h2>Últimas Execuções</h2>
        <ul>
          {runs.map(r => <li key={r.id}>{r.started_at} - {r.status} - {JSON.stringify(r.stats)}</li>)}
        </ul>
      </section>
    </div>
  )
}

createRoot(document.getElementById('root')).render(<App />)