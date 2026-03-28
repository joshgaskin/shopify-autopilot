import React from 'react'

interface DailyInsightProps {
  emoji: string
  text: string
  category: string
}

export default function DailyInsight({ emoji, text, category }: DailyInsightProps) {
  return (
    <div className="bg-accent/5 border border-accent/20 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">{emoji}</span>
        <span className="text-xs font-medium text-accent uppercase tracking-wider">
          {category}
        </span>
      </div>
      <p className="text-sm text-text-primary leading-relaxed">{text}</p>
    </div>
  )
}
