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
    return <div className="text-center text-gray-100">Loading...</div>
  }

  if (error) {
    return <div className="text-center text-red-500">Error: {error}</div>
  }

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="bg-black/50 backdrop-blur-sm rounded-xl shadow-2xl p-6 w-full max-w-md border border-brand/10"
      >
        <h1 className="text-3xl font-bold text-center mb-8 text-brand">Trending Footballers</h1>
        <ul className="space-y-3">
          {footballers.map((footballer, index) => (
            <motion.li
              key={footballer.name}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
              className="bg-black/40 rounded-lg p-4 flex justify-between items-center border border-brand/5 hover:border-brand/20 transition-colors"
            >
              <span className="text-lg font-medium text-gray-100">{footballer.name}</span>
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ duration: 0.3, delay: index * 0.1 + 0.3 }}
                className="flex items-center gap-3"
              >
                <motion.div 
                  className="text-sm font-mono bg-black px-3 py-1.5 rounded-md border border-brand/20 text-brand"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  {footballer.searchInterest}
                </motion.div>
                <motion.div
                  animate={{ 
                    scale: [1, 1.1, 1],
                    rotate: footballer.searchInterest > 5000 ? [0, 5, -5, 0] : 0
                  }}
                  transition={{ 
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                  className="text-xl"
                >
                  {footballer.searchInterest > 30000 ? "🔥" : 
                   footballer.searchInterest > 10000 ? "⚡" : 
                   footballer.searchInterest > 5000 ? "🌟" : "⚽"}
                </motion.div>
              </motion.div>
            </motion.li>
          ))}
        </ul>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 1 }}
          className="text-center mt-6 text-sm text-brand/50"
        >
          Last updated: {lastUpdate || 'Not available'}
        </motion.p>
      </motion.div>
    </div>
  )
}