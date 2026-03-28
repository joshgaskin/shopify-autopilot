import React from 'react'
import Link from 'next/link'
import Shell from '../components/Shell'
import Card from '../components/ui/Card'

const AGENTS = [
  { name: 'Pickle Rick', domain: 'Operations', avatar: '/agents/rick.png', desc: 'Monitors stock health, deactivates dead listings, sends stockout alerts' },
  { name: 'Hank Scorpio', domain: 'Supply Chain', avatar: '/agents/hank.png', desc: 'Scores products, creates purchase orders, manages reorder pipeline' },
  { name: 'Ron Swanson', domain: 'Finance', avatar: '/agents/ron.webp', desc: 'Detects slow movers, creates discount codes, protects margins' },
  { name: 'Marty Supreme', domain: 'Marketing', avatar: '/agents/marty.webp', desc: 'Segments customers, drafts email campaigns, runs win-back plays' },
  { name: 'Marcus Lemonis', domain: 'Chief of Staff', avatar: '/agents/marcus.jpg', desc: 'Coordinates all agents, mediates conflicts, delivers daily insights' },
]

const PLANS = [
  {
    name: 'Starter',
    price: '$49',
    period: '/mo',
    features: ['2 agents (Rick + Hank)', 'Up to 100 products', 'Hourly cycles', 'Email alerts'],
    cta: 'Start free trial',
    highlight: false,
  },
  {
    name: 'Growth',
    price: '$149',
    period: '/mo',
    features: ['All 5 agents', 'Unlimited products', '1-minute cycles', 'Auto discounts + POs', 'Customer segmentation', 'Email campaign drafts'],
    cta: 'Start free trial',
    highlight: true,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: '',
    features: ['Everything in Growth', 'Custom agent personas', 'Dedicated Slack channel', 'API access', 'SOC 2 compliance'],
    cta: 'Talk to us',
    highlight: false,
  },
]

export default function PricingPage() {
  return (
    <Shell title="AutoPilot">
      <div className="space-y-8 max-w-4xl mx-auto">
        {/* Hero */}
        <div className="text-center py-6">
          <h1 className="text-3xl font-bold text-text-primary mb-3">
            Your store runs itself.
          </h1>
          <p className="text-lg text-text-secondary mb-6 max-w-xl mx-auto">
            5 AI agents that monitor, decide, and act on your Shopify store — autonomously, 24/7. Powered by Claude.
          </p>
          <Link
            href="/autopilot"
            className="inline-flex items-center gap-2 bg-accent text-surface-0 px-6 py-2.5 rounded-lg text-sm font-semibold hover:bg-accent/90 transition-colors"
          >
            Open Command Center &rarr;
          </Link>
        </div>

        {/* Meet the Team */}
        <div>
          <h2 className="text-xl font-semibold text-text-primary mb-4">Meet your AI team</h2>
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
            {AGENTS.map((agent) => (
              <Card key={agent.name} className="text-center">
                <img
                  src={agent.avatar}
                  alt={agent.name}
                  className="w-14 h-14 rounded-full object-cover border-2 border-border mx-auto mb-2"
                />
                <h3 className="text-sm font-semibold text-text-primary">{agent.name}</h3>
                <p className="text-xs text-accent mb-1.5">{agent.domain}</p>
                <p className="text-xs text-text-tertiary leading-relaxed">{agent.desc}</p>
              </Card>
            ))}
          </div>
        </div>

        {/* Pricing */}
        <div>
          <h2 className="text-xl font-semibold text-text-primary mb-1">Pricing</h2>
          <p className="text-sm text-text-tertiary mb-4">Start free. Scale when ready.</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {PLANS.map((plan) => (
              <div
                key={plan.name}
                className={`rounded-lg p-5 border ${
                  plan.highlight
                    ? 'border-accent bg-accent/5'
                    : 'border-border bg-surface-1'
                }`}
              >
                <h3 className="text-sm font-semibold text-text-primary">{plan.name}</h3>
                <div className="flex items-baseline gap-0.5 mt-2 mb-3">
                  <span className="text-2xl font-bold text-text-primary">{plan.price}</span>
                  {plan.period && <span className="text-sm text-text-tertiary">{plan.period}</span>}
                </div>
                <ul className="space-y-1.5 mb-4">
                  {plan.features.map((f) => (
                    <li key={f} className="text-xs text-text-secondary flex items-start gap-1.5">
                      <span className="text-accent mt-0.5">&#10003;</span>
                      {f}
                    </li>
                  ))}
                </ul>
                <button
                  className={`w-full text-xs font-medium py-2 rounded-md transition-colors ${
                    plan.highlight
                      ? 'bg-accent text-surface-0 hover:bg-accent/90'
                      : 'bg-surface-2 text-text-secondary hover:text-text-primary'
                  }`}
                >
                  {plan.cta}
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Shell>
  )
}
