'use client'

import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'

interface Footballer {
  name: string
  searchInterest: number
}

export default function TrendingFootballers() {
  const [footballers, setFootballers] = useState<Footballer[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchFootballers = async () => {
      try {
        const response = await fetch('/api/trending-footballers')
        if (!response.ok) {
          throw new Error('Network response was not ok')
        }
        const data: Footballer[] = await response.json()
        setFootballers(data)
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
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="bg-gray-800 rounded-lg shadow-xl p-6 w-full max-w-md"
      >
        <h1 className="text-3xl font-bold text-center mb-6 text-gray-100">Trending Footballers</h1>
        <ul className="space-y-4">
          {footballers.map((footballer, index) => (
            <motion.li
              key={footballer.name}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
              className="bg-gray-700 rounded-lg p-4 flex justify-between items-center"
            >
              <span className="text-lg font-semibold text-gray-200">{footballer.name}</span>
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ duration: 0.3, delay: index * 0.1 + 0.3 }}
                className="bg-gray-900 text-gray-100 rounded-full w-12 h-12 flex items-center justify-center"
              >
                {footballer.searchInterest}
              </motion.div>
            </motion.li>
          ))}
        </ul>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 1 }}
          className="text-center mt-6 text-sm text-gray-400"
        >
          Last updated: {new Date().toLocaleString()}
        </motion.p>
      </motion.div>
    </div>
  )
}