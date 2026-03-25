import React from 'react'

interface BarData {
  label: string
  value: number
  color?: string
}

interface BarChartProps {
  data: BarData[]
  height?: number
  horizontal?: boolean
}

export default function BarChart({
  data,
  height = 200,
  horizontal = false,
}: BarChartProps) {
  if (data.length === 0) return null

  const maxValue = Math.max(...data.map((d) => d.value))

  if (horizontal) {
    const barHeight = 28
    const gap = 8
    const totalHeight = data.length * (barHeight + gap) - gap
    const labelWidth = 120
    const chartWidth = 400

    return (
      <svg
        viewBox={`0 0 ${labelWidth + chartWidth + 60} ${totalHeight}`}
        className="w-full"
        preserveAspectRatio="xMidYMid meet"
      >
        {data.map((d, i) => {
          const barW = maxValue > 0 ? (d.value / maxValue) * chartWidth : 0
          const y = i * (barHeight + gap)
          const color = d.color || '#00FF94'

          return (
            <g key={i}>
              {/* Label */}
              <text
                x={labelWidth - 8}
                y={y + barHeight / 2 + 4}
                textAnchor="end"
                fill="rgba(255,255,255,0.72)"
                fontSize="11"
              >
                {d.label.length > 18 ? d.label.slice(0, 18) + '...' : d.label}
              </text>
              {/* Bar */}
              <rect
                x={labelWidth}
                y={y}
                width={barW}
                height={barHeight}
                rx="4"
                fill={color}
                opacity="0.8"
              />
              {/* Value */}
              <text
                x={labelWidth + barW + 8}
                y={y + barHeight / 2 + 4}
                fill="rgba(255,255,255,0.6)"
                fontSize="11"
              >
                {d.value.toLocaleString()}
              </text>
            </g>
          )
        })}
      </svg>
    )
  }

  // Vertical bars
  const padding = { top: 20, right: 12, bottom: 32, left: 12 }
  const width = 600
  const chartW = width - padding.left - padding.right
  const chartH = height - padding.top - padding.bottom
  const barWidth = Math.min(40, (chartW / data.length) * 0.6)
  const barGap = (chartW - barWidth * data.length) / (data.length + 1)

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full"
      preserveAspectRatio="xMidYMid meet"
    >
      {data.map((d, i) => {
        const barH = maxValue > 0 ? (d.value / maxValue) * chartH : 0
        const x = padding.left + barGap + i * (barWidth + barGap)
        const y = padding.top + chartH - barH
        const color = d.color || '#00FF94'

        return (
          <g key={i}>
            <rect
              x={x}
              y={y}
              width={barWidth}
              height={barH}
              rx="3"
              fill={color}
              opacity="0.8"
            />
            {/* Value on top */}
            <text
              x={x + barWidth / 2}
              y={y - 6}
              textAnchor="middle"
              fill="rgba(255,255,255,0.6)"
              fontSize="10"
            >
              {d.value.toLocaleString()}
            </text>
            {/* Label below */}
            <text
              x={x + barWidth / 2}
              y={height - 8}
              textAnchor="middle"
              fill="rgba(255,255,255,0.35)"
              fontSize="10"
            >
              {d.label.length > 8 ? d.label.slice(0, 8) + '..' : d.label}
            </text>
          </g>
        )
      })}
    </svg>
  )
}
