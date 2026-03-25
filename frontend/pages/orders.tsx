import React, { useState } from 'react'
import Shell from '../components/Shell'
import Card from '../components/ui/Card'
import Tabs from '../components/ui/Tabs'
import Badge from '../components/ui/Badge'
import Modal from '../components/ui/Modal'
import DataTable, { Column } from '../components/DataTable'
import { useOrders } from '../hooks/useOrders'
import { useEventStream } from '../hooks/useEventStream'
import { formatCurrency, formatDate, timeAgo } from '../lib/utils'
import type { Order } from '../lib/types'

// ── Mock Data ──────────────────────────────────────────────────────────────

const MOCK_ORDERS: Order[] = [
  {
    id: '1', order_number: '1042', total_price: 259.99, subtotal_price: 249.99,
    total_discounts: 0, total_tax: 10.00, currency: 'USD',
    financial_status: 'paid', fulfillment_status: 'fulfilled',
    line_items: [{ title: 'The Complete Snowboard', variant_title: 'Default', quantity: 1, price: 249.99 }],
    customer_id: 'c1', customer_email: 'emma.wilson@example.com', customer_name: 'Emma Wilson',
    discount_codes: [], landing_site: '/', referring_site: 'google.com',
    processed_at: '2026-03-24T09:30:00Z', created_at: '2026-03-24T09:30:00Z', is_simulated: false,
  },
  {
    id: '2', order_number: '1041', total_price: 149.50, subtotal_price: 139.50,
    total_discounts: 10.00, total_tax: 10.00, currency: 'USD',
    financial_status: 'paid', fulfillment_status: 'partial',
    line_items: [
      { title: 'Selling Plans Ski Wax', variant_title: 'Premium', quantity: 2, price: 39.99 },
      { title: 'Thermal Base Layer', variant_title: 'M', quantity: 1, price: 49.99 },
    ],
    customer_id: 'c2', customer_email: 'james.chen@example.com', customer_name: 'James Chen',
    discount_codes: ['WELCOME10'], landing_site: '/collections/accessories', referring_site: 'instagram.com',
    processed_at: '2026-03-24T08:15:00Z', created_at: '2026-03-24T08:15:00Z', is_simulated: false,
  },
  {
    id: '3', order_number: '1040', total_price: 89.99, subtotal_price: 89.99,
    total_discounts: 0, total_tax: 0, currency: 'USD',
    financial_status: 'pending', fulfillment_status: 'unfulfilled',
    line_items: [{ title: 'Alpine Goggles', variant_title: 'Default', quantity: 1, price: 89.99 }],
    customer_id: 'c3', customer_email: 'maria.garcia@example.com', customer_name: 'Maria Garcia',
    discount_codes: [], landing_site: '/products/alpine-goggles', referring_site: null,
    processed_at: '2026-03-23T16:45:00Z', created_at: '2026-03-23T16:45:00Z', is_simulated: false,
  },
  {
    id: '4', order_number: '1039', total_price: 324.00, subtotal_price: 299.98,
    total_discounts: 0, total_tax: 24.02, currency: 'USD',
    financial_status: 'paid', fulfillment_status: 'fulfilled',
    line_items: [
      { title: 'Snowboard Boots - Pro', variant_title: 'Size 10', quantity: 1, price: 179.99 },
      { title: 'Thermal Base Layer', variant_title: 'L', quantity: 2, price: 59.99 },
    ],
    customer_id: 'c4', customer_email: 'alex.thompson@example.com', customer_name: 'Alex Thompson',
    discount_codes: [], landing_site: '/', referring_site: 'facebook.com',
    processed_at: '2026-03-23T14:20:00Z', created_at: '2026-03-23T14:20:00Z', is_simulated: false,
  },
  {
    id: '5', order_number: '1038', total_price: 519.98, subtotal_price: 509.98,
    total_discounts: 30.00, total_tax: 40.00, currency: 'USD',
    financial_status: 'refunded', fulfillment_status: 'fulfilled',
    line_items: [
      { title: 'The Collection Snowboard: Hydrogen', variant_title: 'Default', quantity: 2, price: 260.00 },
    ],
    customer_id: 'c5', customer_email: 'sarah.johnson@example.com', customer_name: 'Sarah Johnson',
    discount_codes: ['VIP30'], landing_site: '/collections/snowboards', referring_site: 'tiktok.com',
    processed_at: '2026-03-22T11:00:00Z', created_at: '2026-03-22T11:00:00Z', is_simulated: false,
  },
  {
    id: '6', order_number: '1037', total_price: 74.97, subtotal_price: 74.97,
    total_discounts: 0, total_tax: 0, currency: 'USD',
    financial_status: 'paid', fulfillment_status: 'unfulfilled',
    line_items: [
      { title: 'Selling Plans Ski Wax', variant_title: 'Standard', quantity: 3, price: 24.99 },
    ],
    customer_id: 'c6', customer_email: 'mike.lee@example.com', customer_name: 'Mike Lee',
    discount_codes: [], landing_site: '/products/ski-wax', referring_site: 'google.com',
    processed_at: '2026-03-22T09:30:00Z', created_at: '2026-03-22T09:30:00Z', is_simulated: false,
  },
  {
    id: '7', order_number: '1036', total_price: 449.98, subtotal_price: 429.98,
    total_discounts: 0, total_tax: 20.00, currency: 'USD',
    financial_status: 'paid', fulfillment_status: 'fulfilled',
    line_items: [
      { title: 'The Multi-managed Snowboard', variant_title: 'Large', quantity: 1, price: 329.99 },
      { title: 'Thermal Base Layer', variant_title: 'XL', quantity: 1, price: 69.99 },
    ],
    customer_id: 'c1', customer_email: 'emma.wilson@example.com', customer_name: 'Emma Wilson',
    discount_codes: [], landing_site: '/', referring_site: 'google.com',
    processed_at: '2026-03-21T15:10:00Z', created_at: '2026-03-21T15:10:00Z', is_simulated: false,
  },
  {
    id: '8', order_number: '1035', total_price: 199.99, subtotal_price: 199.99,
    total_discounts: 0, total_tax: 0, currency: 'USD',
    financial_status: 'partially_refunded', fulfillment_status: 'fulfilled',
    line_items: [
      { title: 'The Draft Snowboard', variant_title: 'Default', quantity: 1, price: 199.99 },
    ],
    customer_id: 'c7', customer_email: 'nina.patel@example.com', customer_name: 'Nina Patel',
    discount_codes: [], landing_site: '/products/draft-snowboard', referring_site: null,
    processed_at: '2026-03-21T10:00:00Z', created_at: '2026-03-21T10:00:00Z', is_simulated: false,
  },
]

// ── Page Component ─────────────────────────────────────────────────────────

const statusTabs = [
  { key: 'all', label: 'All' },
  { key: 'paid', label: 'Paid' },
  { key: 'pending', label: 'Pending' },
  { key: 'refunded', label: 'Refunded' },
]

function paymentBadgeVariant(status: string): 'success' | 'warning' | 'error' | 'neutral' {
  switch (status) {
    case 'paid': return 'success'
    case 'pending': return 'warning'
    case 'refunded': case 'partially_refunded': return 'error'
    default: return 'neutral'
  }
}

function fulfillmentBadgeVariant(status: string | null): 'success' | 'warning' | 'error' | 'neutral' {
  switch (status) {
    case 'fulfilled': return 'success'
    case 'partial': return 'warning'
    case 'unfulfilled': return 'error'
    default: return 'neutral'
  }
}

export default function OrdersPage() {
  const [statusFilter, setStatusFilter] = useState('all')
  const [page, setPage] = useState(1)
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null)

  const { data: apiData, error } = useOrders({
    page,
    status: statusFilter === 'all' ? undefined : statusFilter,
  })

  // Track new order IDs from SSE for highlight
  const { events } = useEventStream(10)
  const newOrderNumbers = events
    .filter((e) => e.event_type === 'new_order')
    .map((e) => String(e.payload.order_number))

  const isMock = !!error || !apiData
  const orders = apiData?.data || MOCK_ORDERS
  const totalPages = apiData?.pages || 1

  // Client-side filtering for mock data
  const filtered = isMock
    ? orders.filter((o) => statusFilter === 'all' || o.financial_status === statusFilter)
    : orders

  const columns: Column[] = [
    {
      key: 'order_number',
      label: 'Order',
      sortable: true,
      render: (val: string, row: Order) => (
        <div className="flex items-center gap-2">
          <span className="font-medium">#{val}</span>
          {newOrderNumbers.includes(val) && (
            <span className="w-1.5 h-1.5 rounded-full bg-accent" />
          )}
        </div>
      ),
    },
    {
      key: 'customer_name',
      label: 'Customer',
      render: (val: string | null) => val || 'Guest',
    },
    {
      key: 'total_price',
      label: 'Total',
      sortable: true,
      render: (val: number, row: Order) => formatCurrency(val, row.currency),
    },
    {
      key: 'financial_status',
      label: 'Payment',
      render: (val: string) => (
        <Badge variant={paymentBadgeVariant(val)}>
          {val.charAt(0).toUpperCase() + val.slice(1).replace('_', ' ')}
        </Badge>
      ),
    },
    {
      key: 'fulfillment_status',
      label: 'Fulfillment',
      render: (val: string | null) => (
        <Badge variant={fulfillmentBadgeVariant(val)}>
          {val ? val.charAt(0).toUpperCase() + val.slice(1) : 'Pending'}
        </Badge>
      ),
    },
    {
      key: 'line_items',
      label: 'Items',
      render: (val: any[]) => (
        <span className="text-text-secondary">{val.reduce((s, i) => s + i.quantity, 0)}</span>
      ),
    },
    {
      key: 'created_at',
      label: 'Date',
      sortable: true,
      render: (val: string) => (
        <span className="text-text-secondary">{formatDate(val)}</span>
      ),
    },
  ]

  return (
    <Shell title="Orders">
      {isMock && (
        <div className="bg-status-warning/10 border border-status-warning/20 rounded-lg px-4 py-2 mb-4">
          <span className="text-xs text-status-warning">
            Using demo data — connect to The Pipe for live data
          </span>
        </div>
      )}

      <Card>
        <div className="mb-4">
          <Tabs
            tabs={statusTabs}
            active={statusFilter}
            onChange={(k) => { setStatusFilter(k); setPage(1) }}
          />
        </div>

        <DataTable
          columns={columns}
          data={filtered}
          page={page}
          totalPages={isMock ? 1 : totalPages}
          onPageChange={setPage}
          onRowClick={(row) => setSelectedOrder(row)}
        />
      </Card>

      {/* Order Detail Modal */}
      <Modal
        open={!!selectedOrder}
        onClose={() => setSelectedOrder(null)}
        title={selectedOrder ? `Order #${selectedOrder.order_number}` : ''}
      >
        {selectedOrder && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-xs text-text-tertiary mb-1">Payment</p>
                <Badge variant={paymentBadgeVariant(selectedOrder.financial_status)}>
                  {selectedOrder.financial_status.charAt(0).toUpperCase() + selectedOrder.financial_status.slice(1).replace('_', ' ')}
                </Badge>
              </div>
              <div>
                <p className="text-xs text-text-tertiary mb-1">Fulfillment</p>
                <Badge variant={fulfillmentBadgeVariant(selectedOrder.fulfillment_status)}>
                  {selectedOrder.fulfillment_status
                    ? selectedOrder.fulfillment_status.charAt(0).toUpperCase() + selectedOrder.fulfillment_status.slice(1)
                    : 'Pending'}
                </Badge>
              </div>
              <div>
                <p className="text-xs text-text-tertiary mb-1">Customer</p>
                <p className="text-sm text-text-primary">{selectedOrder.customer_name || 'Guest'}</p>
                {selectedOrder.customer_email && (
                  <p className="text-xs text-text-tertiary">{selectedOrder.customer_email}</p>
                )}
              </div>
              <div>
                <p className="text-xs text-text-tertiary mb-1">Date</p>
                <p className="text-sm text-text-primary">{formatDate(selectedOrder.created_at)}</p>
                <p className="text-xs text-text-tertiary">{timeAgo(selectedOrder.created_at)}</p>
              </div>
            </div>

            {/* Line Items */}
            <div>
              <p className="text-xs text-text-tertiary mb-2">Items</p>
              <div className="space-y-1">
                {selectedOrder.line_items.map((item, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between bg-surface-2 rounded-md px-3 py-2"
                  >
                    <div>
                      <p className="text-sm text-text-primary">{item.title}</p>
                      {item.variant_title && (
                        <p className="text-xs text-text-tertiary">{item.variant_title}</p>
                      )}
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-text-primary">{formatCurrency(item.price * item.quantity)}</p>
                      <p className="text-xs text-text-tertiary">x{item.quantity}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Totals */}
            <div className="border-t border-border pt-3 space-y-1">
              <div className="flex justify-between text-sm">
                <span className="text-text-secondary">Subtotal</span>
                <span className="text-text-primary">{formatCurrency(selectedOrder.subtotal_price)}</span>
              </div>
              {selectedOrder.total_discounts > 0 && (
                <div className="flex justify-between text-sm">
                  <span className="text-text-secondary">Discounts</span>
                  <span className="text-status-success">-{formatCurrency(selectedOrder.total_discounts)}</span>
                </div>
              )}
              {selectedOrder.total_tax > 0 && (
                <div className="flex justify-between text-sm">
                  <span className="text-text-secondary">Tax</span>
                  <span className="text-text-primary">{formatCurrency(selectedOrder.total_tax)}</span>
                </div>
              )}
              <div className="flex justify-between text-sm font-medium pt-1 border-t border-border">
                <span className="text-text-primary">Total</span>
                <span className="text-text-primary">{formatCurrency(selectedOrder.total_price)}</span>
              </div>
            </div>

            {selectedOrder.discount_codes.length > 0 && (
              <div>
                <p className="text-xs text-text-tertiary mb-1">Discount Codes</p>
                <div className="flex gap-1">
                  {selectedOrder.discount_codes.map((code) => (
                    <Badge key={code} variant="neutral">{code}</Badge>
                  ))}
                </div>
              </div>
            )}

            {selectedOrder.referring_site && (
              <div>
                <p className="text-xs text-text-tertiary mb-1">Referred from</p>
                <p className="text-sm text-text-secondary">{selectedOrder.referring_site}</p>
              </div>
            )}
          </div>
        )}
      </Modal>
    </Shell>
  )
}
