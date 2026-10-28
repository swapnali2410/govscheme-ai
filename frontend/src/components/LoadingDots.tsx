export function LoadingDots({ label = 'Working' }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 text-sm text-muted" aria-live="polite">
      <span className="animate-pulse-soft font-medium">{label}</span>
      <span className="flex gap-1">
        <span className="h-1.5 w-1.5 rounded-full bg-leaf animate-pulse-soft" />
        <span
          className="h-1.5 w-1.5 rounded-full bg-leaf animate-pulse-soft"
          style={{ animationDelay: '0.15s' }}
        />
        <span
          className="h-1.5 w-1.5 rounded-full bg-leaf animate-pulse-soft"
          style={{ animationDelay: '0.3s' }}
        />
      </span>
    </div>
  )
}
