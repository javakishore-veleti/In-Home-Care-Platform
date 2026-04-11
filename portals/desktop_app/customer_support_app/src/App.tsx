import { useState } from 'react'

function App() {
  const [search, setSearch] = useState('')

  const cases = [
    { id: 'C-3001', member: 'A. Johnson', issue: 'Reschedule visit', priority: 'Medium', status: 'Open' },
    { id: 'C-3002', member: 'R. Williams', issue: 'Billing question', priority: 'Low', status: 'Open' },
    { id: 'C-3003', member: 'S. Davis', issue: 'Staff complaint', priority: 'High', status: 'Escalated' },
  ]

  const priorityColor: Record<string, string> = {
    High: '#D32F2F', Medium: '#E8A317', Low: '#2D8A4E',
  }
  const statusColor: Record<string, string> = {
    Open: '#1976D2', Escalated: '#D32F2F', Resolved: '#2D8A4E',
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-[#1A2B3C] text-white px-6 py-3 flex items-center gap-3">
        <img src="/logo.svg" alt="Logo" className="h-8 w-8" />
        <h1 className="text-lg font-bold">Customer Support</h1>
        <div className="flex-1" />
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-72 rounded-full border border-white/10 bg-white/12 px-3.5 py-2 text-sm text-white placeholder-[#A7B2BC] focus:outline-none focus:ring-2 focus:ring-[#0D7377]"
          placeholder="Search member by ID, phone, name..."
        />
      </header>

      <div className="flex flex-1">
        {/* Sidebar */}
        <aside className="w-56 bg-[#0D7377] text-white p-4 space-y-2">
          {['Cases', 'Members', 'Visits', 'Appointments', 'Slack #support'].map(item => (
            <button key={item} className="w-full text-left px-3 py-2 rounded hover:bg-[#084C4F] font-medium text-sm">
              {item}
            </button>
          ))}
        </aside>

        {/* Main */}
        <main className="flex-1 p-6">
          <h2 className="text-xl font-bold text-[#0D7377] mb-4">Open Cases</h2>
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#0D7377] text-white">
                <th className="px-4 py-3">Case ID</th>
                <th className="px-4 py-3">Member</th>
                <th className="px-4 py-3">Issue</th>
                <th className="px-4 py-3">Priority</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {cases.map(c => (
                <tr key={c.id} className="border-b border-[#0D7377]/20 hover:bg-[#0D7377]/5 cursor-pointer">
                  <td className="px-4 py-3 font-mono text-sm">{c.id}</td>
                  <td className="px-4 py-3 font-semibold">{c.member}</td>
                  <td className="px-4 py-3">{c.issue}</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-1 rounded text-xs font-bold text-white" style={{ backgroundColor: priorityColor[c.priority] }}>{c.priority}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-1 rounded text-xs font-bold text-white" style={{ backgroundColor: statusColor[c.status] }}>{c.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </main>
      </div>
    </div>
  )
}
export default App
