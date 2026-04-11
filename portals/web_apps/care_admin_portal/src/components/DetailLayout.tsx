import { Link } from 'react-router-dom'
import type { ReactNode } from 'react'

interface DetailLayoutProps {
  title: string
  subtitle?: string
  backTo: string
  backLabel?: string
  loading: boolean
  error: string | null
  children?: ReactNode
}

export function DetailLayout({
  title,
  subtitle,
  backTo,
  backLabel = '← Back',
  loading,
  error,
  children,
}: DetailLayoutProps) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Link
            to={backTo}
            style={{ color: '#0D7377' }}
            className="text-xs font-semibold hover:underline"
          >
            {backLabel}
          </Link>
          <h2 className="text-2xl font-bold text-[#1A2B3C] mt-1">{title}</h2>
          {subtitle && <p className="text-sm text-[#3D5A73] mt-1">{subtitle}</p>}
        </div>
      </div>
      {loading && <p className="text-sm text-[#3D5A73]">Loading...</p>}
      {error && (
        <div className="text-sm text-[#D32F2F] bg-[#FCEAEA] border border-[#D32F2F]/20 rounded px-3 py-2">
          {error}
        </div>
      )}
      {children}
    </div>
  )
}

interface DetailFieldProps {
  label: string
  value: ReactNode
}

export function DetailField({ label, value }: DetailFieldProps) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-wider font-semibold text-[#3D5A73]">{label}</p>
      <p className="text-sm text-[#1A2B3C] mt-1 break-words">{value ?? '—'}</p>
    </div>
  )
}

interface DetailCardProps {
  title?: string
  children: ReactNode
}

export function DetailCard({ title, children }: DetailCardProps) {
  return (
    <div className="bg-white rounded-xl shadow border border-[#0D7377]/10 p-6">
      {title && (
        <h3 className="text-base font-bold text-[#1A2B3C] mb-4 pb-2 border-b border-[#0D7377]/10">
          {title}
        </h3>
      )}
      {children}
    </div>
  )
}
