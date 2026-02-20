import "./global.css"
import Script from "next/script"
import Providers from "@/components/Providers"
import AppShell from "@/components/AppShell"

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <Script
          id="k6-theme-init"
          strategy="beforeInteractive"
          dangerouslySetInnerHTML={{
            __html:
              "(function(){try{var t=localStorage.getItem('k6-theme')||'matrix';var f=localStorage.getItem('k6-font')||'modern';document.documentElement.setAttribute('data-theme',t);document.documentElement.setAttribute('data-font',f);}catch(e){}})();",
          }}
        />
      </head>
      <body className="bg-terminal-bg text-terminal-white">
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  )
}
