import React, { useState } from 'react'
import Shell from '../components/Shell'
import Card from '../components/ui/Card'
import Tabs from '../components/ui/Tabs'
import Badge from '../components/ui/Badge'
import Modal from '../components/ui/Modal'
import DataTable, { Column } from '../components/DataTable'
import { useProducts } from '../hooks/useProducts'
import { formatCurrency, getStatusBg } from '../lib/utils'
import type { Product } from '../lib/types'

// ── Mock Data ──────────────────────────────────────────────────────────────

const MOCK_PRODUCTS: Product[] = [
  {
    id: '1', title: 'The Complete Snowboard', handle: 'complete-snowboard',
    status: 'active', vendor: 'Snowboard Co', product_type: 'Snowboard',
    price_min: 249.99, price_max: 249.99, variants: [
      { id: 'v1', title: 'Default', price: 249.99, sku: 'SB-COMP-001', inventory_quantity: 42 },
    ],
    collections: ['Snowboards'], featured_image_url: null, inventory_total: 42,
    created_at: '2026-01-15T08:00:00Z', updated_at: '2026-03-20T14:00:00Z',
  },
  {
    id: '2', title: 'The Collection Snowboard: Hydrogen', handle: 'hydrogen-snowboard',
    status: 'active', vendor: 'Hydrogen Inc', product_type: 'Snowboard',
    price_min: 260.00, price_max: 260.00, variants: [
      { id: 'v2', title: 'Default', price: 260.00, sku: 'SB-HYD-001', inventory_quantity: 28 },
    ],
    collections: ['Snowboards', 'Collection'], featured_image_url: null, inventory_total: 28,
    created_at: '2026-01-20T08:00:00Z', updated_at: '2026-03-18T10:00:00Z',
  },
  {
    id: '3', title: 'The Multi-managed Snowboard', handle: 'multi-managed-snowboard',
    status: 'active', vendor: 'Multi Manage', product_type: 'Snowboard',
    price_min: 189.99, price_max: 329.99, variants: [
      { id: 'v3a', title: 'Small', price: 189.99, sku: 'SB-MM-S', inventory_quantity: 15 },
      { id: 'v3b', title: 'Large', price: 329.99, sku: 'SB-MM-L', inventory_quantity: 8 },
    ],
    collections: ['Snowboards'], featured_image_url: null, inventory_total: 23,
    created_at: '2026-02-01T08:00:00Z', updated_at: '2026-03-22T09:00:00Z',
  },
  {
    id: '4', title: 'The Draft Snowboard', handle: 'draft-snowboard',
    status: 'draft', vendor: 'Snowboard Co', product_type: 'Snowboard',
    price_min: 199.99, price_max: 199.99, variants: [
      { id: 'v4', title: 'Default', price: 199.99, sku: 'SB-DFT-001', inventory_quantity: 50 },
    ],
    collections: [], featured_image_url: null, inventory_total: 50,
    created_at: '2026-03-01T08:00:00Z', updated_at: '2026-03-15T11:00:00Z',
  },
  {
    id: '5', title: 'Selling Plans Ski Wax', handle: 'ski-wax',
    status: 'active', vendor: 'Wax World', product_type: 'Accessories',
    price_min: 24.99, price_max: 39.99, variants: [
      { id: 'v5a', title: 'Standard', price: 24.99, sku: 'WAX-STD', inventory_quantity: 120 },
      { id: 'v5b', title: 'Premium', price: 39.99, sku: 'WAX-PRM', inventory_quantity: 85 },
    ],
    collections: ['Accessories'], featured_image_url: null, inventory_total: 205,
    created_at: '2026-01-10T08:00:00Z', updated_at: '2026-03-23T16:00:00Z',
  },
  {
    id: '6', title: 'Snowboard Boots - Pro', handle: 'boots-pro',
    status: 'active', vendor: 'Boot Masters', product_type: 'Boots',
    price_min: 179.99, price_max: 219.99, variants: [
      { id: 'v6a', title: 'Size 9', price: 179.99, sku: 'BT-PRO-9', inventory_quantity: 18 },
      { id: 'v6b', title: 'Size 10', price: 179.99, sku: 'BT-PRO-10', inventory_quantity: 22 },
      { id: 'v6c', title: 'Size 11', price: 219.99, sku: 'BT-PRO-11', inventory_quantity: 14 },
    ],
    collections: ['Boots', 'Footwear'], featured_image_url: null, inventory_total: 54,
    created_at: '2026-02-05T08:00:00Z', updated_at: '2026-03-21T12:00:00Z',
  },
  {
    id: '7', title: 'Alpine Goggles', handle: 'alpine-goggles',
    status: 'archived', vendor: 'ViewClear', product_type: 'Accessories',
    price_min: 89.99, price_max: 89.99, variants: [
      { id: 'v7', title: 'Default', price: 89.99, sku: 'GOG-ALP', inventory_quantity: 0 },
    ],
    collections: ['Accessories'], featured_image_url: null, inventory_total: 0,
    created_at: '2025-11-01T08:00:00Z', updated_at: '2026-02-10T08:00:00Z',
  },
  {
    id: '8', title: 'Thermal Base Layer', handle: 'thermal-base-layer',
    status: 'active', vendor: 'WarmTech', product_type: 'Apparel',
    price_min: 49.99, price_max: 69.99, variants: [
      { id: 'v8a', title: 'S', price: 49.99, sku: 'TBL-S', inventory_quantity: 30 },
      { id: 'v8b', title: 'M', price: 49.99, sku: 'TBL-M', inventory_quantity: 45 },
      { id: 'v8c', title: 'L', price: 59.99, sku: 'TBL-L', inventory_quantity: 38 },
      { id: 'v8d', title: 'XL', price: 69.99, sku: 'TBL-XL', inventory_quantity: 20 },
    ],
    collections: ['Apparel'], featured_image_url: null, inventory_total: 133,
    created_at: '2026-01-25T08:00:00Z', updated_at: '2026-03-19T15:00:00Z',
  },
]

// ── Page Component ─────────────────────────────────────────────────────────

const statusTabs = [
  { key: 'all', label: 'All' },
  { key: 'active', label: 'Active' },
  { key: 'draft', label: 'Draft' },
  { key: 'archived', label: 'Archived' },
]

function getStatusBadgeVariant(status: string): 'success' | 'warning' | 'error' | 'neutral' {
  switch (status) {
    case 'active': return 'success'
    case 'draft': return 'warning'
    case 'archived': return 'error'
    default: return 'neutral'
  }
}

export default function ProductsPage() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [page, setPage] = useState(1)
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)

  const { data: apiData, error } = useProducts({
    page,
    search: search || undefined,
    status: statusFilter === 'all' ? undefined : statusFilter,
  })

  const isMock = !!error || !apiData
  const products = apiData?.data || MOCK_PRODUCTS
  const totalPages = apiData?.pages || 1

  // Client-side filtering for mock data
  const filtered = isMock
    ? products.filter((p) => {
        const matchesSearch = !search || p.title.toLowerCase().includes(search.toLowerCase())
        const matchesStatus = statusFilter === 'all' || p.status === statusFilter
        return matchesSearch && matchesStatus
      })
    : products

  const columns: Column[] = [
    {
      key: 'title',
      label: 'Product',
      sortable: true,
      render: (_val: any, row: Product) => (
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-surface-2 rounded border border-border flex items-center justify-center text-text-tertiary text-xs">
            {row.featured_image_url ? (
              <img src={row.featured_image_url} alt="" className="w-full h-full object-cover rounded" />
            ) : (
              row.title.charAt(0)
            )}
          </div>
          <span className="font-medium">{row.title}</span>
        </div>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (val: string) => (
        <Badge variant={getStatusBadgeVariant(val)}>
          {val.charAt(0).toUpperCase() + val.slice(1)}
        </Badge>
      ),
    },
    {
      key: 'price_min',
      label: 'Price',
      sortable: true,
      render: (_val: any, row: Product) =>
        row.price_min === row.price_max
          ? formatCurrency(row.price_min)
          : `${formatCurrency(row.price_min)} - ${formatCurrency(row.price_max)}`,
    },
    {
      key: 'inventory_total',
      label: 'Inventory',
      sortable: true,
      render: (val: number) => (
        <span className={val === 0 ? 'text-status-error' : ''}>{val} in stock</span>
      ),
    },
    {
      key: 'product_type',
      label: 'Type',
    },
    {
      key: 'vendor',
      label: 'Vendor',
    },
  ]

  return (
    <Shell title="Products">
      {isMock && (
        <div className="bg-status-warning/10 border border-status-warning/20 rounded-lg px-4 py-2 mb-4">
          <span className="text-xs text-status-warning">
            Using demo data — connect to The Pipe for live data
          </span>
        </div>
      )}

      <Card>
        {/* Search + Tabs */}
        <div className="mb-4">
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            placeholder="Search products..."
            className="w-full bg-surface-2 border border-border rounded-md px-3 py-2 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-border-active mb-3"
          />
          <Tabs tabs={statusTabs} active={statusFilter} onChange={(k) => { setStatusFilter(k); setPage(1) }} />
        </div>

        <DataTable
          columns={columns}
          data={filtered}
          page={page}
          totalPages={isMock ? 1 : totalPages}
          onPageChange={setPage}
          onRowClick={(row) => setSelectedProduct(row)}
        />
      </Card>

      {/* Product Detail Modal */}
      <Modal
        open={!!selectedProduct}
        onClose={() => setSelectedProduct(null)}
        title={selectedProduct?.title || ''}
      >
        {selectedProduct && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-xs text-text-tertiary mb-1">Status</p>
                <Badge variant={getStatusBadgeVariant(selectedProduct.status)}>
                  {selectedProduct.status.charAt(0).toUpperCase() + selectedProduct.status.slice(1)}
                </Badge>
              </div>
              <div>
                <p className="text-xs text-text-tertiary mb-1">Vendor</p>
                <p className="text-sm text-text-primary">{selectedProduct.vendor}</p>
              </div>
              <div>
                <p className="text-xs text-text-tertiary mb-1">Type</p>
                <p className="text-sm text-text-primary">{selectedProduct.product_type}</p>
              </div>
              <div>
                <p className="text-xs text-text-tertiary mb-1">Total Inventory</p>
                <p className="text-sm text-text-primary">{selectedProduct.inventory_total}</p>
              </div>
            </div>

            {/* Variants */}
            <div>
              <p className="text-xs text-text-tertiary mb-2">Variants ({selectedProduct.variants.length})</p>
              <div className="space-y-1">
                {selectedProduct.variants.map((v) => (
                  <div
                    key={v.id}
                    className="flex items-center justify-between bg-surface-2 rounded-md px-3 py-2"
                  >
                    <div>
                      <p className="text-sm text-text-primary">{v.title}</p>
                      <p className="text-xs text-text-tertiary">{v.sku}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-text-primary">{formatCurrency(v.price)}</p>
                      <p className="text-xs text-text-tertiary">{v.inventory_quantity} in stock</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {selectedProduct.collections.length > 0 && (
              <div>
                <p className="text-xs text-text-tertiary mb-1">Collections</p>
                <div className="flex flex-wrap gap-1">
                  {selectedProduct.collections.map((c) => (
                    <Badge key={c} variant="neutral">{c}</Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </Shell>
  )
}
