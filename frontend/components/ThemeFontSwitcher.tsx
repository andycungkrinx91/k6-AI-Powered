"use client"

import { useMemo, useState } from "react"
import Modal from "@/components/Modal"
import { Palette } from "lucide-react"

type ThemeId =
  | "matrix"
  | "amber"
  | "cyberpunk"
  | "midnight"
  | "modern-geist"
  | "modern-linear"
  | "terminal-terminator"
  | "terminal-arch"
type FontId = "modern" | "classic" | "geometric" | "retro"

const THEMES: { id: ThemeId; label: string; hint: string }[] = [
  { id: "matrix", label: "matrix", hint: "linux green" },
  { id: "amber", label: "amber", hint: "mainframe" },
  { id: "cyberpunk", label: "cyberpunk", hint: "neon" },
  { id: "midnight", label: "midnight", hint: "dracula" },
  { id: "modern-geist", label: "modern/geist", hint: "clean contrast" },
  { id: "modern-linear", label: "modern/linear", hint: "sleek indigo" },
  { id: "terminal-terminator", label: "terminal/terminator", hint: "utilitarian red" },
  { id: "terminal-arch", label: "terminal/arch", hint: "arch blue" },
]

const FONTS: { id: FontId; label: string; hint: string }[] = [
  { id: "modern", label: "modern", hint: "dev mono" },
  { id: "classic", label: "classic", hint: "dense" },
  { id: "geometric", label: "geometric", hint: "wide" },
  { id: "retro", label: "retro", hint: "crt" },
]

function getAttr(name: string, fallback: string) {
  if (typeof document === "undefined") return fallback
  return document.documentElement.getAttribute(name) || fallback
}

function getStored(key: "theme" | "font", fallback: string) {
  if (typeof window === "undefined") return fallback
  try {
    return window.localStorage.getItem(`k6-${key}`) || fallback
  } catch {
    return fallback
  }
}

function setPref(key: "theme" | "font", value: string) {
  if (typeof document === "undefined") return
  document.documentElement.setAttribute(`data-${key}`, value)
  try {
    window.localStorage.setItem(`k6-${key}`, value)
  } catch {
    // ignore
  }
}

export default function ThemeFontSwitcher({
  compact,
}: {
  compact?: boolean
}) {
  const [open, setOpen] = useState(false)
  // Initial theme/font are read from <html data-theme/data-font>, which is
  // set by the beforeInteractive script in `frontend/app/layout.tsx`.
  const [theme, setTheme] = useState<ThemeId>(() => getAttr("data-theme", "matrix") as ThemeId)
  const [font, setFont] = useState<FontId>(() => getAttr("data-font", "modern") as FontId)

  const activeTheme = useMemo(() => THEMES.find((t) => t.id === theme), [theme])
  const activeFont = useMemo(() => FONTS.find((f) => f.id === font), [font])

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className={
          compact
            ? "px-2.5 py-2 border border-terminal-border text-terminal-white hover:bg-terminal-surface2 rounded-md flex items-center gap-2"
            : "px-4 py-2 border border-terminal-border text-terminal-white hover:bg-terminal-surface2 rounded-md"
        }
      >
        {compact ? (
          <>
            <Palette size={14} className="text-terminal-dim" />
            <span className="text-[11px] uppercase tracking-widest text-terminal-dim">theme</span>
          </>
        ) : (
          `theme: ${activeTheme?.label}/${activeFont?.label}`
        )}
      </button>

      {open && (
        <Modal title="Theme settings" onClose={() => setOpen(false)}>
          <div className="space-y-6">
            <div className="text-xs text-terminal-dim">
              Configure theme + font. Persisted in local storage.
            </div>

            <div className="space-y-3">
              <div className="text-terminal-white text-sm">&gt; SELECT THEME</div>
              <div className="grid grid-cols-2 gap-2">
                {THEMES.map((t) => {
                  const selected = t.id === theme
                  return (
                    <button
                      key={t.id}
                      onClick={() => {
                        setTheme(t.id)
                        setPref("theme", t.id)
                      }}
                      className={
                        selected
                          ? "border border-terminal-phosphor bg-terminal-phosphor/15 text-terminal-phosphor px-3 py-2 text-left"
                          : "border border-terminal-border bg-terminal-bg text-terminal-white px-3 py-2 text-left hover:bg-terminal-surface2"
                      }
                    >
                      <div className="text-xs">
                        {selected ? "[*]" : "[ ]"} {t.label}
                      </div>
                      <div className="text-[11px] text-terminal-dim">{t.hint}</div>
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="space-y-3">
              <div className="text-terminal-white text-sm">&gt; SELECT FONT</div>
              <div className="grid grid-cols-2 gap-2">
                {FONTS.map((f) => {
                  const selected = f.id === font
                  return (
                    <button
                      key={f.id}
                      onClick={() => {
                        setFont(f.id)
                        setPref("font", f.id)
                      }}
                      className={
                        selected
                          ? "border border-terminal-cyan bg-terminal-cyan/10 text-terminal-cyan px-3 py-2 text-left"
                          : "border border-terminal-border bg-terminal-bg text-terminal-white px-3 py-2 text-left hover:bg-terminal-surface2"
                      }
                    >
                      <div className="text-xs">
                        {selected ? "[*]" : "[ ]"} {f.label}
                      </div>
                      <div className="text-[11px] text-terminal-dim">{f.hint}</div>
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="pt-2 border-t border-terminal-border flex items-center justify-between">
              <div className="text-xs text-terminal-dim">status: OK</div>
              <button
                onClick={() => setOpen(false)}
                className="px-4 py-2 border border-terminal-phosphor text-terminal-phosphor hover:bg-terminal-phosphor hover:text-black"
              >
                [ CLOSE ]
              </button>
            </div>
          </div>
        </Modal>
      )}
    </>
  )
}
