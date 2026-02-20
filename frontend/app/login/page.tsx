"use client"

import { FormEvent, useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/context/AuthContext"
import { motion, Variants } from "framer-motion"

const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.12,
    },
  },
}

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 18 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.55, ease: [0.16, 1, 0.3, 1] },
  },
}

const pageVariants: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.35 } },
}

function AsciiBrand() {
  return (
    <div className="max-w-full overflow-x-auto">
      <pre className="text-[7px] leading-[9px] text-terminal-magenta select-none whitespace-pre">
{String.raw`

                                               :
                                               :::                 :
                                               :::-               ::-
                                               :::-             ::::-
                                              ::::=:          ::::::=
                                            :-:::--       :-:::::::-:        :
                                           -=:::--     :-=-::::::--        ::::
                                          ==-----==:-=*=---------:       =-::::
                                        :=+-=--====**=--------==-:...:=+-::::-:
                               :-:     -+*=====+##+====----===-::=+*+=:::::::-
                            -%%+--::::-+#+**++#%+++++======+*%%#+--------::-= -
                           +@%=========---+*#%*++++++++*#%%*=-------------==-
                          #@#+==========+*=-******++*%%*+========-------==-
                        =+=***++++++++++****+=****#%%*+++=++++=======+=-
                           :=#%@%++++++*******+*+#@**++++++++==========-
                               *@%++++++++++++++=##****++++++++++++=--
                               +@@*****++++++++**#********++++=:
                               +@@##*****++*******###*#***+++++=
                               +@@####************###+=---
                               -%@################+==+++-              :=+=:
                                =@@##########*+=====++++*%%=         =%#-:-+#*:
                                 -%@*+##*+==----====++++++%@%+      -%+      -#-
                                   =@@#+*####**+*********+*#@%%=     %#-.-*...+#
                         ::::        -%@%****######%%%%%%%%%%%%%*     =##+....+#
                 ::-======+++++*+-      =#@#+=----==+*#%%%%%%%%%%%:          -#:
                 :+#*****+--=******=       :-+#%%*+-    ::+#@%%%#*=         +*:
                    =#######*=::+####                            -###*-..-##:  =+++=-::+%%%
                     -#########*=:-*#+            :                 -=+*+-   :----:   :#*+@:
                       *########%#=:-*              ::-++*****#**+=-:  -*#%#*=---=*%#+  ::
                        -#%%%%%%%%%#      --                     :+#%%*-             *%-
                           -+**++-           :====--::::--=+*##*+=:                   +%-
                                        :-          :::::::      :=+***+-      -#%#*  -%=
                                           -*+-         :-+*%%%#+-     :+%#:   %#     ##:
                                                :--====--:   :            =%=  +%*--=%#:
                                                  :---====-::        --    *%:   -++-:
                                                                   =%#-=   ##
                                                                   +%-    +%-
                                                                    *%#*#%*:
`}
      </pre>
    </div>
  )
}

function LogStream() {
  const lines = [
    "[OK] k6.engine: performance test runner online",
    "[OK] security.headers: scan pipeline ready",
    "[OK] ssl.tls: certificate + protocol analysis ready",
    "[OK] wpt.playwright: first/repeat view collection ready",
    "[OK] lighthouse.audit: perf/accessibility/seo ready",
    "[OK] report.pdf: generation pipeline enabled",
    "[OK] result.store: mysql persistence active",
    "[HINT] admin/user roles: dashboard access scoped",
  ]

  return (
    <div className="relative mt-6 overflow-hidden border border-terminal-border bg-terminal-surface2 p-4">
      <div className="absolute inset-0 opacity-[0.08] [background-image:radial-gradient(rgba(57,255,20,0.8)_1px,transparent_1px)] [background-size:18px_18px]" />
      <div className="relative font-mono text-xs leading-5 text-terminal-dim">
        {lines.map((text, idx) => (
          <motion.div
            key={text}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.15 + idx * 0.08, duration: 0.25 }}
          >
            {text}
          </motion.div>
        ))}
      </div>
    </div>
  )
}

export default function LoginPage() {
  const { login, ready, user } = useAuth()
  const router = useRouter()
  const [identifier, setIdentifier] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    if (ready && user) {
      router.replace("/")
    }
  }, [ready, user, router])

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError("")
    setLoading(true)

    try {
      await login({ identifier, password })
      router.replace("/")
    } catch (err: any) {
      setError(err?.message || "Unable to sign in")
    } finally {
      setLoading(false)
    }
  }

  if (!ready) {
    return (
      <div className="min-h-screen bg-terminal-bg flex items-center justify-center">
        <motion.div
          animate={{ opacity: [0.55, 1, 0.55] }}
          transition={{ repeat: Infinity, duration: 1.6 }}
          className="text-sm font-medium tracking-widest uppercase text-terminal-phosphor"
        >
          Loading...
        </motion.div>
      </div>
    )
  }

  return (
    <motion.div variants={pageVariants} initial="hidden" animate="visible" className="min-h-screen">
      <div className="min-h-screen grid lg:grid-cols-2">
        <div className="relative hidden lg:block border-r border-terminal-border bg-terminal-bg">
          <div className="absolute inset-0 opacity-[0.14] [background-image:linear-gradient(to_bottom,rgba(57,255,20,0.14),transparent_60%),radial-gradient(rgba(57,255,20,0.35)_1px,transparent_1px)] [background-size:auto,22px_22px]" />
          <div className="relative h-full p-12 flex flex-col justify-center">
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45 }}
              className="space-y-5"
            >
              <div className="text-terminal-dim text-xs tracking-widest uppercase">secure access terminal</div>
              <div className="text-terminal-phosphor text-3xl font-semibold">K6 AI Powered</div>
              <div className="text-terminal-white/80 text-sm max-w-md leading-relaxed">
                Authenticate to run load tests, generate reports, and track results. Admins can provision users.
              </div>
              <AsciiBrand />
              <LogStream />
            </motion.div>
          </div>
        </div>

        <div className="relative bg-terminal-bg flex items-center justify-center px-5 py-10">
          <div className="absolute inset-0 opacity-[0.10] [background-image:radial-gradient(rgba(0,255,255,0.7)_1px,transparent_1px)] [background-size:28px_28px]" />

          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="relative w-full max-w-md"
          >
            <div className="border border-terminal-border bg-terminal-surface shadow-terminal">
              <div className="flex items-center justify-between border-b border-terminal-border px-5 py-3">
                <div className="text-terminal-dim text-xs">[ SYSTEM AUTHENTICATION REQUIRED ]</div>
                <div className="text-terminal-dim text-xs">tty:01</div>
              </div>

              <div className="p-6 sm:p-8 space-y-6">
                <motion.div variants={itemVariants} className="space-y-1">
                  <div className="text-terminal-phosphor text-xl font-semibold">login</div>
                  <div className="text-terminal-dim text-xs">enter credentials to start session</div>
                </motion.div>

                {error && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    className="border border-terminal-magenta/40 bg-terminal-magenta/10 px-4 py-3 text-sm text-terminal-magenta"
                  >
                    [ERR] {error}
                  </motion.div>
                )}

                <form onSubmit={handleSubmit} className="space-y-5">
                  <motion.div variants={itemVariants} className="space-y-2">
                    <label className="text-terminal-dim text-xs uppercase tracking-widest">[ username_or_email ]</label>
                    <div className="flex items-center gap-3 border border-terminal-border bg-terminal-bg px-3 py-2">
                      <span className="text-terminal-dim text-xs">&gt;</span>
                      <input
                        value={identifier}
                        onChange={(event) => setIdentifier(event.target.value)}
                        className="w-full bg-transparent border-0 px-0 py-0 focus:ring-0"
                        placeholder="andy or andy@example.com"
                        autoComplete="username"
                      />
                    </div>
                  </motion.div>

                  <motion.div variants={itemVariants} className="space-y-2">
                    <label className="text-terminal-dim text-xs uppercase tracking-widest">[ password ]</label>
                    <div className="flex items-center gap-3 border border-terminal-border bg-terminal-bg px-3 py-2">
                      <span className="text-terminal-dim text-xs">&gt;</span>
                      <input
                        type="password"
                        value={password}
                        onChange={(event) => setPassword(event.target.value)}
                        className="w-full bg-transparent border-0 px-0 py-0 focus:ring-0"
                        placeholder="••••••••"
                        autoComplete="current-password"
                      />
                    </div>
                  </motion.div>

                  <motion.div variants={itemVariants} className="pt-1">
                    <button
                      type="submit"
                      disabled={loading}
                      className="w-full border border-terminal-phosphor text-terminal-phosphor bg-transparent px-4 py-3 text-sm font-semibold uppercase tracking-widest hover:bg-terminal-phosphor hover:text-black disabled:opacity-60"
                    >
                      {loading ? "> INIT_SESSION..." : "> INIT_SESSION"}
                    </button>
                  </motion.div>
                </form>

                <motion.div variants={itemVariants} className="text-xs text-terminal-dim border-t border-terminal-border pt-4">
                  tip: contact admin if you cannot sign in.
                </motion.div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </motion.div>
  )
}
