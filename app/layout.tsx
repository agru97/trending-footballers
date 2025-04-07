import React from 'react'
import './globals.css'
import { Inter } from 'next/font/google'
import { Navigation } from './components/Navigation'

const inter = Inter({ subsets: ['latin'] })

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  themeColor: '#4D96FF',
}

export const metadata = {
  title: 'Trending Footballers',
  description: 'Track real-time popularity and trending status of football players worldwide',
  manifest: '/manifest.json',
  icons: {
    apple: [
      { url: '/apple-touch-icon.png' },
      { url: '/apple-touch-icon-precomposed.png' }
    ]
  },
  themeColor: '#4D96FF'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <meta name="theme-color" content="#4D96FF" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <link rel="manifest" href="/manifest.json" />
      </head>
      <body className={`${inter.className} overflow-x-hidden bg-[#4D96FF]`}>
        <Navigation />
        <main className="min-h-screen w-full">
          {children}
        </main>
      </body>
    </html>
  )
}
