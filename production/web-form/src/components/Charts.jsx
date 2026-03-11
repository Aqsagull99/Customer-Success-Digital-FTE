export function LineChart({ points = [], stroke = 'currentColor' }) {
  const max = Math.max(...points, 1)
  const min = Math.min(...points, 0)
  const range = max - min || 1
  const path = points
    .map((value, index) => {
      const x = (index / (points.length - 1 || 1)) * 100
      const y = 100 - ((value - min) / range) * 100
      return `${index === 0 ? 'M' : 'L'} ${x} ${y}`
    })
    .join(' ')

  return (
    <svg className="chart chart--line" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
      <path d={path} fill="none" stroke={stroke} strokeWidth="2.5" />
      <path d={`${path} L 100 100 L 0 100 Z`} fill="url(#lineFill)" opacity="0.35" />
      <defs>
        <linearGradient id="lineFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={stroke} />
          <stop offset="100%" stopColor="transparent" />
        </linearGradient>
      </defs>
    </svg>
  )
}

export function DonutChart({ segments = [] }) {
  const total = segments.reduce((sum, seg) => sum + seg.value, 0) || 1
  let cumulative = 0

  return (
    <svg className="chart chart--donut" viewBox="0 0 42 42" aria-hidden="true">
      <circle className="chart__track" cx="21" cy="21" r="15.915" />
      {segments.map((seg) => {
        const dash = (seg.value / total) * 100
        const gap = 100 - dash
        const rotation = (cumulative / total) * 360
        cumulative += seg.value
        return (
          <circle
            key={seg.label}
            className="chart__segment"
            cx="21"
            cy="21"
            r="15.915"
            stroke={seg.color}
            strokeDasharray={`${dash} ${gap}`}
            strokeDashoffset="25"
            transform={`rotate(${rotation} 21 21)`}
          />
        )
      })}
      <circle className="chart__hole" cx="21" cy="21" r="9.5" />
    </svg>
  )
}

export function BarChart({ bars = [] }) {
  const max = Math.max(...bars.map((b) => b.value), 1)
  return (
    <div className="chart chart--bar">
      {bars.map((bar) => (
        <div key={bar.label} className="bar">
          <div className="bar__fill" style={{ height: `${(bar.value / max) * 100}%`, background: bar.color }} />
          <span className="bar__label">{bar.label}</span>
        </div>
      ))}
    </div>
  )
}
