"use client"

import { ReactNode } from "react"

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
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="relative w-full max-w-md rounded-2xl bg-white shadow-xl p-6">

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
        >
          ✕
        </button>

        {/* Title */}
        {title && (
          <h2 className="text-xl font-semibold mb-4">
            {title}
          </h2>
        )}

        {/* Content */}
        <div>{children}</div>
      </div>
    </div>
  )
}
