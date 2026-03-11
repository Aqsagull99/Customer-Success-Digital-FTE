import { IconMail, IconPhone, IconGlobe } from '../components/Icons'

export default function Settings() {
  return (
    <div className="page-transition">
      <div className="page-header">
        <div>
          <p className="pill">SETTINGS</p>
          <h1 className="heading heading--hero">Workspace Settings</h1>
          <p className="subheading subheading--hero">Manage profile preferences and notifications.</p>
        </div>
      </div>

      <div className="settings-grid">
        <div className="settings-card">
          <h3 className="card-title">Profile</h3>
          <p className="card-subtitle">Keep your contact details up to date.</p>
          <div className="profile-row">
            <div className="avatar">AK</div>
            <div>
              <p className="profile-name">Ayesha Khan</p>
              <p className="profile-meta">Product Lead</p>
            </div>
          </div>
          <div className="form-grid">
            <div>
              <label className="label">Name</label>
              <input className="field" defaultValue="Ayesha Khan" />
            </div>
            <div>
              <label className="label">Email</label>
              <input className="field" defaultValue="ayesha@techcorp.com" />
            </div>
          </div>
        </div>

        <div className="settings-card">
          <h3 className="card-title">Notifications</h3>
          <p className="card-subtitle">Control alerts for new and escalated tickets.</p>
          <div className="toggle-list">
            {[
              'New ticket assigned',
              'Ticket escalated',
              'Daily summary digest',
            ].map((label) => (
              <label key={label} className="toggle-row">
                <span>{label}</span>
                <span className="toggle">
                  <input type="checkbox" defaultChecked />
                  <span className="toggle-slider" />
                </span>
              </label>
            ))}
          </div>
        </div>

        <div className="settings-card">
          <h3 className="card-title">Default reply channel</h3>
          <p className="card-subtitle">Set the preferred response channel.</p>
          <div className="channel-grid">
            {[
              { label: 'Email', icon: <IconMail /> },
              { label: 'WhatsApp', icon: <IconPhone /> },
              { label: 'Web Portal', icon: <IconGlobe /> },
            ].map((item) => (
              <button key={item.label} type="button" className="channel-pill">
                <span className="channel-icon">{item.icon}</span>
                {item.label}
              </button>
            ))}
          </div>
        </div>

        <div className="settings-card">
          <h3 className="card-title">Theme</h3>
          <p className="card-subtitle">Switch between light and dark palettes.</p>
          <div className="filter-tabs">
            {['Light', 'Dark'].map((label) => (
              <button key={label} type="button" className="filter-tab">
                {label}
              </button>
            ))}
          </div>
        </div>

        <div className="settings-card">
          <h3 className="card-title">Security</h3>
          <p className="card-subtitle">Update your password regularly.</p>
          <button type="button" className="btn-primary">Change password</button>
        </div>
      </div>
    </div>
  )
}
