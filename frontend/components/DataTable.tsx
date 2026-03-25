import React, { useState } from 'react'
import { cn } from '../lib/utils'
import Button from './ui/Button'

export interface Column {
  key: string
  label: string
  sortable?: boolean
  render?: (value: any, row: any) => React.ReactNode
}

interface DataTableProps {
  columns: Column[]
  data: any[]
  onSort?: (key: string, direction: 'asc' | 'desc') => void
  page?: number
  totalPages?: number
  onPageChange?: (page: number) => void
  onRowClick?: (row: any) => void
}

export default function DataTable({
  columns,
  data,
  onSort,
  page = 1,
  totalPages = 1,
  onPageChange,
  onRowClick,
}: DataTableProps) {
  const [sortKey, setSortKey] = useState<string | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  const handleSort = (key: string) => {
    const newDir = sortKey === key && sortDir === 'asc' ? 'desc' : 'asc'
    setSortKey(key)
    setSortDir(newDir)
    onSort?.(key, newDir)
  }

  return (
    <div className="w-full">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={cn(
                    'px-3 py-2.5 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider bg-surface-1',
                    col.sortable && 'cursor-pointer select-none hover:text-text-secondary'
                  )}
                  onClick={() => col.sortable && handleSort(col.key)}
                >
                  <div className="flex items-center gap-1">
                    {col.label}
                    {col.sortable && sortKey === col.key && (
                      <svg width="10" height="10" viewBox="0 0 10 10" className="text-text-secondary">
                        {sortDir === 'asc' ? (
                          <path d="M5 2l3 4H2l3-4z" fill="currentColor" />
                        ) : (
                          <path d="M5 8l3-4H2l3 4z" fill="currentColor" />
                        )}
                      </svg>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, rowIndex) => (
              <tr
                key={row.id || rowIndex}
                className={cn(
                  'border-b border-border transition-colors duration-150 ease-out',
                  rowIndex % 2 === 1 && 'bg-surface-1/30',
                  onRowClick && 'cursor-pointer hover:bg-surface-2'
                )}
                onClick={() => onRowClick?.(row)}
              >
                {columns.map((col) => (
                  <td key={col.key} className="px-3 py-2.5 text-sm text-text-primary">
                    {col.render
                      ? col.render(row[col.key], row)
                      : row[col.key]}
                  </td>
                ))}
              </tr>
            ))}
            {data.length === 0 && (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-3 py-8 text-center text-sm text-text-tertiary"
                >
                  No data found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && onPageChange && (
        <div className="flex items-center justify-between px-3 py-3 border-t border-border">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
          >
            Previous
          </Button>
          <span className="text-xs text-text-tertiary">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  )
}
