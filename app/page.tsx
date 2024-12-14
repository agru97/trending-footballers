'use client'

import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'

interface Footballer {
  name: string
  searchInterest: number
}

export default function TrendingFootballers() {
  const [footballers, setFootballers] = useState<Footballer[]>([])
  const [lastUpdate, setLastUpdate] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const handlePlayerClick = (playerName: string) => {
    const searchQuery = encodeURIComponent(playerName + ' footballer')
    window.open(`https://www.google.com/search?q=${searchQuery}`, '_blank')
  }

  useEffect(() => {
    const fetchFootballers = async () => {
      try {
        const response = await fetch('/api/trending-footballers')
        if (!response.ok) {
          throw new Error('Network response was not ok')
        }
        const data = await response.json()
        setFootballers(data.footballers)
        setLastUpdate(data.lastUpdate)
      } catch (err: any) {
        setError(err.message || 'An error occurred')
      } finally {
        setLoading(false)
      }
    }

    fetchFootballers()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-brand/30 via-brand/5 to-brand/20 flex items-center justify-center p-4">
        <div className="text-center text-gray-600">Loading...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-brand/30 via-brand/5 to-brand/20 flex items-center justify-center p-4">
        <div className="text-center text-red-500">Error: {error}</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand/30 via-brand/5 to-brand/20 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="relative bg-white/90 backdrop-blur-lg rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.06)] p-8 w-full max-w-md border border-brand/5"
      >
        <div className="absolute -top-12 left-1/2 transform -translate-x-1/2">
          <div className="bg-brand text-white text-sm py-2 px-4 rounded-full shadow-lg">
            Live Rankings
          </div>
        </div>
        <h1 className="text-4xl font-bold text-center mb-8 bg-gradient-to-r from-brand to-blue-700 text-transparent bg-clip-text">
          Trending Footballers
        </h1>
        <ul className="space-y-4">
          {footballers.map((footballer, index) => (
            <li
              key={footballer.name}
              onClick={() => handlePlayerClick(footballer.name)}
              className="bg-white rounded-xl p-4 flex justify-between items-center border border-brand/5 hover:border-brand/20 transition-all hover:shadow-md hover:-translate-y-0.5 cursor-pointer"
            >
              <span className="text-lg font-medium text-gray-800 flex items-center gap-3">
                <span className="text-brand/30">{index + 1}</span>
                {footballer.name}
              </span>
              <div className="text-sm font-mono bg-gradient-to-r from-brand/5 to-brand/10 px-4 py-2 rounded-lg border border-brand/10 text-brand font-semibold">
                {footballer.searchInterest}
              </div>
            </li>
          ))}
        </ul>
        <p className="text-center mt-8 text-sm text-gray-500">
          Last updated: {lastUpdate || 'Not available'}
        </p>
      </motion.div>
    </div>
  )
}