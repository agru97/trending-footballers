import './globals.css'

export const metadata = {
  title: 'Footballer Search Tracker',
  description: 'Real-time football player trends and statistics',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
