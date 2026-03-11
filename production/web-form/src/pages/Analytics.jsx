import DashboardCard from '../components/DashboardCard'
import { LineChart, DonutChart, BarChart } from '../components/Charts'
import { IconBolt, IconClock, IconShield, IconTicket } from '../components/Icons'

const metrics = [
  { title: 'Total Tickets (Month)', value: '312', subtext: 'Up 12% vs last month', icon: <IconTicket /> },
  { title: 'Avg Response Time', value: '2m 40s', subtext: 'Target 3m', icon: <IconClock /> },
  { title: 'Resolution Rate', value: '96%', subtext: 'Last 30 days', icon: <IconShield /> },
  { title: 'Active Agents', value: '18', subtext: 'Currently online', icon: <IconBolt /> },
]

const linePoints = [30, 42, 38, 50, 46, 60, 54, 68, 62, 70, 76, 72]

const statusSegments = [
  { label: 'Open', value: 38, color: 'var(--accent)' },
  { label: 'In Progress', value: 24, color: 'var(--accent-2)' },
  { label: 'Closed', value: 64, color: 'var(--accent-3)' },
]

const priorityBars = [
  { label: 'Low', value: 42, color: 'color-mix(in srgb, var(--accent) 60%, transparent)' },
  { label: 'Medium', value: 60, color: 'color-mix(in srgb, var(--accent-2) 60%, transparent)' },
  { label: 'High', value: 26, color: 'color-mix(in srgb, var(--accent-3) 65%, transparent)' },
]

export default function Analytics() {
  return (
    <div className="page-transition">
      <div className="page-header">
        <div>
          <p className="pill">ANALYTICS</p>
          <h1 className="heading heading--hero">Performance Insights</h1>
          <p className="subheading subheading--hero">Track response velocity and ticket health.</p>
        </div>
      </div>

      <div className="grid-stats">
        {metrics.map((item) => (
          <DashboardCard
            key={item.title}
            title={item.title}
            value={item.value}
            subtext={item.subtext}
            icon={item.icon}
          />
        ))}
      </div>

      <div className="charts-grid">
        <div className="chart-card">
          <h3 className="card-title">Tickets trend</h3>
          <p className="card-subtitle">Monthly incoming tickets</p>
          <LineChart points={linePoints} stroke="var(--accent)" />
        </div>
        <div className="chart-card">
          <h3 className="card-title">Status breakdown</h3>
          <p className="card-subtitle">Open vs in progress vs closed</p>
          <div className="chart-inline">
            <DonutChart segments={statusSegments} />
            <div className="legend">
              {statusSegments.map((seg) => (
                <div key={seg.label} className="legend-item">
                  <span className="legend-dot" style={{ background: seg.color }} />
                  {seg.label}
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="chart-card">
          <h3 className="card-title">Priority split</h3>
          <p className="card-subtitle">Ticket urgency distribution</p>
          <BarChart bars={priorityBars} />
        </div>
      </div>
    </div>
  )
}
