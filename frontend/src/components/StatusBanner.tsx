interface StatusBannerProps {
  type: 'error' | 'success' | 'info'
  message: string
  onDismiss?: () => void
}

export function StatusBanner({ type, message, onDismiss }: StatusBannerProps) {
  const styles =
    type === 'error'
      ? 'border-danger/30 bg-danger/10 text-danger'
      : type === 'success'
        ? 'border-ok/30 bg-ok/10 text-ok'
        : 'border-leaf/25 bg-leaf/10 text-forest'

  return (
    <div
      className={`animate-fade-up flex items-start justify-between gap-3 rounded-xl border px-4 py-3 text-sm ${styles}`}
      role="status"
    >
      <p className="leading-relaxed">{message}</p>
      {onDismiss ? (
        <button
          type="button"
          onClick={onDismiss}
          className="shrink-0 text-xs font-semibold uppercase tracking-wide opacity-70 hover:opacity-100"
        >
          Dismiss
        </button>
      ) : null}
    </div>
  )
}
