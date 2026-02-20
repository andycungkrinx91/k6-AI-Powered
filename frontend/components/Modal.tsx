"use client"

import { ReactNode } from "react"
import { createPortal } from "react-dom"

type ModalProps = {
  children: ReactNode
  onClose: () => void
  title?: string
}

export default function Modal({
  children,
  onClose,
  title,
}: ModalProps) {
  // This component is only rendered in response to client interactions.
  // Avoid setState-in-effect just to detect mount; guard on DOM availability instead.
  if (typeof document === "undefined") return null

  const content = (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-lg border border-terminal-border bg-terminal-surface shadow-terminal p-6 rounded-md">

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-terminal-dim hover:text-terminal-white"
        >
          ✕
        </button>

        {/* Title */}
        {title && (
          <h2 className="text-xl font-semibold mb-4 text-terminal-phosphor">
            {title}
          </h2>
        )}

        {/* Content */}
        <div>{children}</div>
      </div>
    </div>
  )

  return createPortal(content, document.body)
}
