import DashboardCard from '../components/DashboardCard'
import DataTable from '../components/DataTable'
import { IconBolt, IconClock, IconShield, IconTicket } from '../components/Icons'

const summary = [
  { title: 'All Tickets', value: '1,284', subtext: 'Total volume', icon: <IconTicket /> },
  { title: 'Open', value: '128', subtext: 'Needs triage', icon: <IconClock /> },
  { title: 'In Progress', value: '46', subtext: 'Assigned', icon: <IconBolt /> },
  { title: 'Closed', value: '1,110', subtext: 'Completed', icon: <IconShield /> },
]

const tickets = [
  { id: 'TK-1024', name: 'Ayesha Khan', subject: 'Login MFA reset', priority: 'High', status: 'Open', date: 'Mar 4, 2026' },
  { id: 'TK-1023', name: 'Umair Saeed', subject: 'Invoice mismatch', priority: 'Medium', status: 'In Progress', date: 'Mar 3, 2026' },
  { id: 'TK-1022', name: 'Maria Lee', subject: 'API timeout issue', priority: 'High', status: 'Open', date: 'Mar 3, 2026' },
  { id: 'TK-1021', name: 'David Park', subject: 'Plan upgrade', priority: 'Low', status: 'Closed', date: 'Mar 2, 2026' },
  { id: 'TK-1020', name: 'Sara Malik', subject: 'SSO setup help', priority: 'Medium', status: 'Closed', date: 'Mar 2, 2026' },
  { id: 'TK-1019', name: 'Omar Farooq', subject: 'Payment failed retry', priority: 'High', status: 'In Progress', date: 'Mar 1, 2026' },
]

const columns = [
  { key: 'id', label: 'ID' },
  { key: 'name', label: 'Customer Name' },
  { key: 'subject', label: 'Subject' },
  {
    key: 'priority',
    label: 'Priority',
    render: (row) => <span className={`badge badge--${row.priority.toLowerCase()}`}>{row.priority}</span>,
  },
  {
    key: 'status',
    label: 'Status',
    render: (row) => <span className={`badge badge--status badge--${row.status.toLowerCase().replace(' ', '-')}`}>{row.status}</span>,
  },
  { key: 'date', label: 'Created' },
  {
    key: 'action',
    label: 'Action',
    render: () => <button type="button" className="btn-ghost btn-ghost--sm">View</button>,
  },
]

export default function Tickets() {
  return (
    <div className="page-transition">
      <div className="page-header">
        <div>
          <p className="pill">TICKETS</p>
          <h1 className="heading heading--hero">Ticket Queue</h1>
          <p className="subheading subheading--hero">Search, filter, and manage active support tickets.</p>
        </div>
        <button type="button" className="btn-primary">Create Ticket</button>
      </div>

      <div className="filter-row">
        <div className="search-field">
          <input className="field" placeholder="Search tickets by customer, ID, or subject" />
        </div>
        <div className="filter-tabs" role="tablist" aria-label="Ticket status">
          {['All', 'Open', 'In Progress', 'Closed'].map((label) => (
            <button key={label} type="button" className="filter-tab">
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid-stats">
        {summary.map((item) => (
          <DashboardCard
            key={item.title}
            title={item.title}
            value={item.value}
            subtext={item.subtext}
            icon={item.icon}
          />
        ))}
      </div>

      <div className="section">
        <div className="section-head">
          <h2 className="section-title">All tickets</h2>
          <p className="section-subtitle">Latest requests across all channels.</p>
        </div>
        <DataTable columns={columns} rows={tickets} />
      </div>
    </div>
  )
}
