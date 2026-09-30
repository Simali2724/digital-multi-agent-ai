import type { Metadata } from "next"

import "./globals.css"

export const metadata: Metadata = {
  title: "Reliance Digital AI Assistant",
  description:
    "Multi-Agent Sales and resQ support assistant for Reliance Digital",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
    >
      <body suppressHydrationWarning>
        {children}
      </body>
    </html>
  )
}