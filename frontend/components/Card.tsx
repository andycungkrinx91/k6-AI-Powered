export default function Card({
  title,
  children,
}: {
  title?: string
  children: React.ReactNode
}) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
      {title && (
        <h2 className="text-lg font-semibold mb-6">
          {title}
        </h2>
      )}
      {children}
    </div>
  )
}
