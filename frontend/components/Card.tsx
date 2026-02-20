export default function Card({
  title,
  children,
}: {
  title?: string
  children: React.ReactNode
}) {
  return (
    <div className="bg-terminal-surface border border-terminal-border shadow-terminal p-4 sm:p-6 rounded-md">
      {title && (
        <h2 className="text-base sm:text-lg font-semibold mb-4 sm:mb-6 break-words text-terminal-phosphor">
          {title}
        </h2>
      )}
      {children}
    </div>
  )
}
