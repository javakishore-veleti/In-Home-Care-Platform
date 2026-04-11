function App() {
  const stats = [
    { label: "Today's Visits", value: 12, color: '#0D7377' },
    { label: 'Open Appointments', value: 8, color: '#E8612D' },
    { label: 'Staff Available', value: 15, color: '#2D8A4E' },
    { label: 'Pending Reviews', value: 3, color: '#1976D2' },
  ]
  const recentVisits = [
    { id: 'V-1001', member: 'A. Johnson', staff: 'Maria R.', type: 'Skilled Nursing', status: 'Completed' },
    { id: 'V-1002', member: 'R. Williams', staff: 'James P.', type: 'Physical Therapy', status: 'In Progress' },
    { id: 'V-1003', member: 'S. Davis', staff: 'Pending', type: 'Home Health Aide', status: 'Scheduled' },
  ]
  const statusColor: Record<string, string> = {
    Completed: 'bg-[#2D8A4E]', 'In Progress': 'bg-[#E8A317]', Scheduled: 'bg-[#1976D2]',
  }
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-[#1A2B3C] text-white px-6 py-4 flex items-center gap-3 shadow-lg">
        <img src="/logo.svg" alt="Logo" className="h-10 w-10" />
        <h1 className="text-xl font-bold">Care Admin Portal</h1>
      </header>
      <main className="flex-1 p-8 max-w-6xl mx-auto w-full">
        <h2 className="text-2xl font-bold text-[#0D7377] mb-6">Dashboard</h2>
        <div className="grid grid-cols-4 gap-6 mb-8">
          {stats.map(s => (
            <div key={s.label} className="rounded-xl p-6 text-white shadow-md" style={{ backgroundColor: s.color }}>
              <p className="text-3xl font-bold">{s.value}</p>
              <p className="text-sm font-medium mt-1">{s.label}</p>
            </div>
          ))}
        </div>
        <h3 className="text-xl font-bold text-[#1A2B3C] mb-4">Recent Visits</h3>
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-[#0D7377] text-white">
              <th className="px-4 py-3 rounded-tl-lg">ID</th>
              <th className="px-4 py-3">Member</th>
              <th className="px-4 py-3">Staff</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3 rounded-tr-lg">Status</th>
            </tr>
          </thead>
          <tbody>
            {recentVisits.map(v => (
              <tr key={v.id} className="border-b border-[#0D7377]/20 hover:bg-[#0D7377]/5">
                <td className="px-4 py-3 font-mono text-sm">{v.id}</td>
                <td className="px-4 py-3 font-semibold">{v.member}</td>
                <td className="px-4 py-3">{v.staff}</td>
                <td className="px-4 py-3">{v.type}</td>
                <td className="px-4 py-3">
                  <span className={`px-3 py-1 rounded-full text-xs font-bold text-white ${statusColor[v.status] || ''}`}>{v.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </main>
      <footer className="bg-[#1A2B3C] text-white text-center py-4 text-sm">Care Admin Portal &copy; 2026</footer>
    </div>
  )
}
export default App
