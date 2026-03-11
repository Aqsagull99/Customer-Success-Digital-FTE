export default function DashboardCard({ title, value, subtext, icon }) {
  return (
    <div className="dash-card">
      <div className="dash-card__top">
        <div className="dash-card__icon">{icon}</div>
        <div>
          <p className="dash-card__title">{title}</p>
          <p className="dash-card__value">{value}</p>
        </div>
      </div>
      {subtext && <p className="dash-card__subtext">{subtext}</p>}
    </div>
  )
}
