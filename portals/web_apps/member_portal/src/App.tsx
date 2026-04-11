import { useState } from 'react'

function App() {
  const [page, setPage] = useState<'home' | 'book' | 'visits' | 'login'>('home')

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-[#0D7377] text-white px-6 py-4 flex items-center justify-between shadow-lg">
        <div className="flex items-center gap-3">
          <img src="/logo.svg" alt="Logo" className="h-10 w-10" />
          <h1 className="text-xl font-bold tracking-tight">In-Home Care</h1>
        </div>
        <nav className="flex gap-4 text-sm font-medium">
          <button onClick={() => setPage('home')} className={`px-3 py-1 rounded ${page === 'home' ? 'bg-[#084C4F]' : 'hover:bg-[#11999E]'}`}>Home</button>
          <button onClick={() => setPage('book')} className={`px-3 py-1 rounded ${page === 'book' ? 'bg-[#084C4F]' : 'hover:bg-[#11999E]'}`}>Book Appointment</button>
          <button onClick={() => setPage('visits')} className={`px-3 py-1 rounded ${page === 'visits' ? 'bg-[#084C4F]' : 'hover:bg-[#11999E]'}`}>My Visits</button>
          <button onClick={() => setPage('login')} className="bg-[#E8612D] hover:bg-[#C44A1C] px-4 py-1 rounded font-semibold">Sign In</button>
        </nav>
      </header>

      {/* Main */}
      <main className="flex-1 p-8 max-w-5xl mx-auto w-full">
        {page === 'home' && <HomePage onBook={() => setPage('book')} />}
        {page === 'book' && <BookPage />}
        {page === 'visits' && <VisitsPage />}
        {page === 'login' && <LoginPage />}
      </main>

      {/* Footer */}
      <footer className="bg-[#1A2B3C] text-white text-center py-4 text-sm">
        In-Home Care Platform &copy; 2026
      </footer>
    </div>
  )
}

function HomePage({ onBook }: { onBook: () => void }) {
  return (
    <div className="text-center py-16">
      <img src="/logo.svg" alt="Logo" className="h-24 w-24 mx-auto mb-6" />
      <h2 className="text-3xl font-bold text-[#0D7377] mb-4">Welcome to In-Home Care</h2>
      <p className="text-lg text-[#3D5A73] mb-8 max-w-xl mx-auto">
        Quality healthcare delivered to your home. Book an appointment,
        track your visits, and stay connected with your care team.
      </p>
      <button onClick={onBook}
        className="bg-[#E8612D] hover:bg-[#C44A1C] text-white text-lg font-semibold px-8 py-3 rounded-lg shadow-md transition-colors">
        Book an Appointment
      </button>
    </div>
  )
}

function BookPage() {
  return (
    <div>
      <h2 className="text-2xl font-bold text-[#0D7377] mb-6">Book an Appointment</h2>
      <form className="space-y-5 max-w-lg">
        <div>
          <label className="block text-sm font-semibold text-[#1A2B3C] mb-1">Service Type</label>
          <select className="w-full border-2 border-[#0D7377] rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#11999E]">
            <option>Home Health Aide</option>
            <option>Skilled Nursing</option>
            <option>Physical Therapy</option>
            <option>Companion Care</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-semibold text-[#1A2B3C] mb-1">Preferred Date</label>
          <input type="date" className="w-full border-2 border-[#0D7377] rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#11999E]" />
        </div>
        <div>
          <label className="block text-sm font-semibold text-[#1A2B3C] mb-1">Preferred Time</label>
          <select className="w-full border-2 border-[#0D7377] rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#11999E]">
            <option>Morning (8am - 12pm)</option>
            <option>Afternoon (12pm - 4pm)</option>
            <option>Evening (4pm - 8pm)</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-semibold text-[#1A2B3C] mb-1">Notes</label>
          <textarea rows={3} className="w-full border-2 border-[#0D7377] rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#11999E]" placeholder="Any special requirements..." />
        </div>
        <button type="button" className="bg-[#E8612D] hover:bg-[#C44A1C] text-white font-semibold px-6 py-3 rounded-lg shadow-md w-full transition-colors">
          Confirm Appointment
        </button>
      </form>
    </div>
  )
}

function VisitsPage() {
  const visits = [
    { id: 'V-1001', date: '2026-04-08', type: 'Skilled Nursing', status: 'Completed', staff: 'Maria R.' },
    { id: 'V-1002', date: '2026-04-12', type: 'Physical Therapy', status: 'Scheduled', staff: 'James P.' },
    { id: 'V-1003', date: '2026-04-15', type: 'Home Health Aide', status: 'Scheduled', staff: 'Pending' },
  ]
  const statusColor: Record<string, string> = {
    Completed: 'bg-[#2D8A4E] text-white',
    Scheduled: 'bg-[#1976D2] text-white',
    'In Progress': 'bg-[#E8A317] text-white',
    Cancelled: 'bg-[#D32F2F] text-white',
  }
  return (
    <div>
      <h2 className="text-2xl font-bold text-[#0D7377] mb-6">My Visits</h2>
      <div className="space-y-4">
        {visits.map(v => (
          <div key={v.id} className="border-2 border-[#0D7377] rounded-lg p-5 flex justify-between items-center">
            <div>
              <p className="font-bold text-[#1A2B3C]">{v.type}</p>
              <p className="text-sm text-[#3D5A73]">{v.date} &middot; {v.staff}</p>
            </div>
            <span className={`px-3 py-1 rounded-full text-xs font-bold ${statusColor[v.status] || ''}`}>
              {v.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function LoginPage() {
  return (
    <div className="max-w-md mx-auto py-12">
      <h2 className="text-2xl font-bold text-[#0D7377] mb-6 text-center">Sign In</h2>
      <form className="space-y-4">
        <div>
          <label className="block text-sm font-semibold text-[#1A2B3C] mb-1">Email</label>
          <input type="email" className="w-full border-2 border-[#0D7377] rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#11999E]" placeholder="you@example.com" />
        </div>
        <div>
          <label className="block text-sm font-semibold text-[#1A2B3C] mb-1">Password</label>
          <input type="password" className="w-full border-2 border-[#0D7377] rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#11999E]" />
        </div>
        <button type="button" className="bg-[#0D7377] hover:bg-[#084C4F] text-white font-semibold px-6 py-3 rounded-lg shadow-md w-full transition-colors">
          Sign In
        </button>
        <p className="text-center text-sm text-[#3D5A73]">
          Don't have an account? <a href="#" className="text-[#E8612D] font-semibold hover:underline">Sign Up</a>
        </p>
      </form>
    </div>
  )
}

export default App
