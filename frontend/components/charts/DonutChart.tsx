import React from 'react'

interface Segment {
  label: string
  value: number
  color: string
}

interface DonutChartProps {
  segments: Segment[]
  size?: number
  thickness?: number
  centerLabel?: string
  centerValue?: string
}

export default function DonutChart({
  segments,
  size = 160,
  thickness = 20,
  centerLabel,
  centerValue,
}: DonutChartProps) {
  const total = segments.reduce((sum, s) => sum + s.value, 0)
  if (total === 0) return null

  const radius = (size - thickness) / 2
  const circumference = 2 * Math.PI * radius
  const center = size / 2

  let cumulativeOffset = 0
  const arcs = segments.map((seg) => {
    const pct = seg.value / total
    const dashLength = pct * circumference
    const offset = cumulativeOffset
    cumulativeOffset += dashLength
    return { ...seg, dashLength, offset, pct }
  })

  return (
    <div className="flex flex-col items-center gap-3">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Background ring */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.05)"
          strokeWidth={thickness}
        />
        {/* Segments */}
        {arcs.map((arc, i) => (
          <circle
            key={i}
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke={arc.color}
            strokeWidth={thickness}
            strokeDasharray={`${arc.dashLength} ${circumference - arc.dashLength}`}
            strokeDashoffset={-arc.offset}
            strokeLinecap="butt"
            transform={`rotate(-90 ${center} ${center})`}
            opacity="0.85"
          />
        ))}
        {/* Center text */}
        {centerValue && (
          <text
            x={center}
            y={center - 4}
            textAnchor="middle"
            fill="rgba(255,255,255,0.95)"
            fontSize="18"
            fontWeight="600"
          >
            {centerValue}
          </text>
        )}
        {centerLabel && (
          <text
            x={center}
            y={center + 14}
            textAnchor="middle"
            fill="rgba(255,255,255,0.48)"
            fontSize="10"
          >
            {centerLabel}
          </text>
        )}
      </svg>
      {/* Legend */}
      <div className="flex flex-wrap justify-center gap-x-4 gap-y-1">
        {arcs.map((arc, i) => (
          <div key={i} className="flex items-center gap-1.5">
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: arc.color }}
            />
            <span className="text-xs text-text-secondary">
              {arc.label} ({Math.round(arc.pct * 100)}%)
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
