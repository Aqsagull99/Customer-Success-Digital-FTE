import { useEffect, useState } from 'react'
import { NavLink, Route, Routes, useLocation } from 'react-router-dom'
import Overview from './pages/Overview'
import Tickets from './pages/Tickets'
import Analytics from './pages/Analytics'
import Settings from './pages/Settings'
import Chat from './pages/Chat'
import ChatWidget from './components/ChatWidget'
import {
  IconOverview,
  IconAnalytics,
  IconSettings,
  IconTicket,
  IconChat,
} from './components/Icons'

// Scroll restoration fix
function ScrollToTop() {
  const { pathname } = useLocation();

  useEffect(() => {
    // Disable scroll restoration
    if ('scrollRestoration' in window.history) {
      window.history.scrollRestoration = 'manual';
    }
    // Scroll to top on route change
    window.scrollTo(0, 0);
  }, [pathname]);

  return null;
}

const THEMES = [
  { id: 'paper', label: 'Paper' },
  { id: 'sunrise', label: 'Sunrise' },
  { id: 'ocean', label: 'Ocean' },
  { id: 'noir', label: 'Noir' },
]

function App() {
  const [theme, setTheme] = useState('paper')
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  return (
    <div className="page app-shell">
      <ScrollToTop />
      <div className={`app-overlay ${sidebarOpen ? 'is-visible' : ''}`} onClick={() => setSidebarOpen(false)} />
      <aside className={`sidebar ${sidebarOpen ? 'is-open' : ''}`}>
        <div className="sidebar-glow" />
        <div className="sidebar-inner">
          <div className="logo-row">
            <div className="logo-glow" />
            <div className="logo-mark" aria-hidden="true" />
            <div className="logo-text">TechCorp</div>
            <button
              type="button"
              className="sidebar-close"
              aria-label="Close navigation"
              onClick={() => setSidebarOpen(false)}
            >
              <span />
              <span />
            </button>
          </div>
          <div className="soft-divider" />
          <nav className="sidebar-nav" aria-label="Primary">
            {[
              { label: 'Overview', icon: IconOverview },
              { label: 'Tickets', icon: IconTicket },
              { label: 'Chat', icon: IconChat },
              { label: 'Analytics', icon: IconAnalytics },
              { label: 'Settings', icon: IconSettings },
            ].map(({ label, icon: Icon }, index) => (
              <NavLink
                key={label}
                to={label === 'Overview' ? '/' : `/${label.toLowerCase()}`}
                end={label === 'Overview'}
                className={({ isActive }) => `nav-item ${isActive ? 'is-active' : ''}`}
                style={{ '--stagger': `${index * 60}ms` }}
                onClick={() => setSidebarOpen(false)}
              >
                <span className="nav-icon" aria-hidden="true">
                  <Icon className="icon icon--sm" />
                </span>
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>
          <div className="sidebar-spacer" />
          <div className="soft-divider" />
          <div className="theme-block">
            <p className="theme-label">Theme</p>
            <div className="theme-switcher theme-switcher--sidebar" role="radiogroup" aria-label="Theme switcher">
              {THEMES.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  aria-pressed={theme === item.id}
                  onClick={() => setTheme(item.id)}
                  className={`theme-chip ${theme === item.id ? 'theme-chip--active' : ''}`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </aside>

      <div className="page-main">
        <div className="page-content">
          <div className="mobile-topbar">
            <button
              type="button"
              className="sidebar-toggle"
              aria-label="Open navigation"
              onClick={() => setSidebarOpen(true)}
            >
              <span />
              <span />
              <span />
            </button>
            <p className="pill">CUSTOMER SUPPORT</p>
          </div>
          <Routes>
            <Route index element={<Overview />} />
            <Route path="/tickets" element={<Tickets />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </div>
      </div>

      <ChatWidget />
    </div>
  )
}

export default App
