import React, { useState, useRef } from 'react'

interface DataPoint {
  label: string
  value: number
}

interface LineChartProps {
  data: DataPoint[]
  height?: number
  color?: string
  showGrid?: boolean
  showLabels?: boolean
  showTooltip?: boolean
}

export default function LineChart({
  data,
  height = 200,
  color = '#00FF94',
  showGrid = true,
  showLabels = true,
  showTooltip = true,
}: LineChartProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)
  const svgRef = useRef<SVGSVGElement>(null)

  if (data.length < 2) return null

  const padding = { top: 12, right: 12, bottom: showLabels ? 28 : 8, left: 12 }
  const width = 600
  const chartW = width - padding.left - padding.right
  const chartH = height - padding.top - padding.bottom

  const values = data.map((d) => d.value)
  const min = Math.min(...values) * 0.9
  const max = Math.max(...values) * 1.1
  const range = max - min || 1

  const points = data.map((d, i) => ({
    x: padding.left + (i / (data.length - 1)) * chartW,
    y: padding.top + chartH - ((d.value - min) / range) * chartH,
  }))

  // Build smooth cubic bezier path
  let pathD = `M ${points[0].x.toFixed(1)} ${points[0].y.toFixed(1)}`
  for (let i = 1; i < points.length; i++) {
    const prev = points[i - 1]
    const curr = points[i]
    const cpx = (prev.x + curr.x) / 2
    pathD += ` C ${cpx.toFixed(1)} ${prev.y.toFixed(1)}, ${cpx.toFixed(1)} ${curr.y.toFixed(1)}, ${curr.x.toFixed(1)} ${curr.y.toFixed(1)}`
  }

  // Area fill path
  const areaD = `${pathD} L ${points[points.length - 1].x.toFixed(1)} ${(padding.top + chartH).toFixed(1)} L ${points[0].x.toFixed(1)} ${(padding.top + chartH).toFixed(1)} Z`

  // Grid lines (4 horizontal)
  const gridLines = showGrid
    ? [0.25, 0.5, 0.75].map((pct) => padding.top + chartH * (1 - pct))
    : []

  // Label spacing: show at most 7 labels
  const labelStep = Math.max(1, Math.floor(data.length / 7))

  return (
    <svg
      ref={svgRef}
      viewBox={`0 0 ${width} ${height}`}
      className="w-full"
      preserveAspectRatio="xMidYMid meet"
    >
      <defs>
        <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.12" />
          <stop offset="100%" stopColor={color} stopOpacity="0.01" />
        </linearGradient>
      </defs>

      {/* Grid lines */}
      {gridLines.map((y, i) => (
        <line
          key={i}
          x1={padding.left}
          y1={y}
          x2={width - padding.right}
          y2={y}
          stroke="rgba(255,255,255,0.05)"
          strokeWidth="1"
        />
      ))}

      {/* Area fill */}
      <path d={areaD} fill="url(#areaGrad)" />

      {/* Line */}
      <path d={pathD} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />

      {/* X-axis labels */}
      {showLabels &&
        data.map((d, i) =>
          i % labelStep === 0 || i === data.length - 1 ? (
            <text
              key={i}
              x={points[i].x}
              y={height - 4}
              textAnchor="middle"
              fill="rgba(255,255,255,0.35)"
              fontSize="10"
            >
              {d.label}
            </text>
          ) : null
        )}

      {/* Hover zones */}
      {showTooltip &&
        points.map((p, i) => (
          <g key={i}>
            <rect
              x={
                i === 0
                  ? padding.left
                  : (points[i - 1].x + p.x) / 2
              }
              y={padding.top}
              width={
                i === 0 || i === points.length - 1
                  ? chartW / data.length / 2
                  : (points[Math.min(i + 1, points.length - 1)].x - points[Math.max(i - 1, 0)].x) / 2
              }
              height={chartH}
              fill="transparent"
              onMouseEnter={() => setHoveredIndex(i)}
              onMouseLeave={() => setHoveredIndex(null)}
            />
          </g>
        ))}

      {/* Tooltip */}
      {hoveredIndex !== null && (
        <g>
          <line
            x1={points[hoveredIndex].x}
            y1={padding.top}
            x2={points[hoveredIndex].x}
            y2={padding.top + chartH}
            stroke="rgba(255,255,255,0.15)"
            strokeWidth="1"
            strokeDasharray="3,3"
          />
          <circle
            cx={points[hoveredIndex].x}
            cy={points[hoveredIndex].y}
            r="4"
            fill={color}
            stroke="#0A0A0B"
            strokeWidth="2"
          />
          <rect
            x={points[hoveredIndex].x - 35}
            y={points[hoveredIndex].y - 28}
            width="70"
            height="20"
            rx="4"
            fill="#222225"
            stroke="rgba(255,255,255,0.08)"
            strokeWidth="1"
          />
          <text
            x={points[hoveredIndex].x}
            y={points[hoveredIndex].y - 14}
            textAnchor="middle"
            fill="rgba(255,255,255,0.95)"
            fontSize="11"
            fontWeight="500"
          >
            {data[hoveredIndex].value.toLocaleString()}
          </text>
        </g>
      )}
    </svg>
  )
}
