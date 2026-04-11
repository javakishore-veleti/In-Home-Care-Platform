import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { HashRouter } from 'react-router-dom'

import './index.css'
import App from './App'
import { AuthProvider } from './context/AuthContext'

// HashRouter is used because the desktop bundle is loaded from a file:// URL
// in Electron — BrowserRouter would 404 on refresh inside the packaged app.
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <HashRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </HashRouter>
  </StrictMode>,
)
