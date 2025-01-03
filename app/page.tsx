'use client'

import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import countryCodes from '../public/country-codes.json'

interface Footballer {
  name: string
  searchInterest: number
  full_name: string
  nationality: string
  club: string
  club_logo: string
  player_photo: string
}

// Helper function to convert country name to ISO code
function getCountryCode(nationality: string): string {
  const countryCodesReverse = Object.entries(countryCodes)
    .reduce<{ [key: string]: string }>((acc, [code, name]) => {
      acc[name.toLowerCase()] = code;
      return acc;
    }, {});

  return countryCodesReverse[nationality.toLowerCase()] || nationality.toLowerCase();
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

    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchFootballers, 300000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-[#4D96FF] flex items-center justify-center p-4">
        <div className="text-center text-white">
          <svg className="animate-spin h-8 w-8 mb-4 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <div className="text-xl font-medium">Fetching latest trends...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#4D96FF] flex items-center justify-center p-4">
        <div className="text-center bg-white/90 p-6 rounded-xl shadow-lg">
          <div className="text-red-500 text-xl mb-2">Oops! Something went wrong</div>
          <div className="text-gray-600">{error}</div>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-4 px-4 py-2 bg-brand text-white rounded-lg"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen w-full bg-brand flex items-center justify-center p-4 sm:p-6 md:p-8">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="relative bg-white/95 backdrop-blur-xl rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.12)] p-6 sm:p-8 w-full max-w-md border border-white/20"
      >
        <motion.div 
          className="absolute -top-3 sm:-top-4 left-0 right-0 mx-auto w-fit"
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <div className="bg-gradient-to-r from-brand to-blue-600 text-white text-sm py-2 px-4 rounded-full shadow-lg flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-white"></span>
            </span>
            Live Rankings
          </div>
        </motion.div>
        <h1 className="text-3xl sm:text-4xl font-bold text-center mb-2 bg-gradient-to-r from-brand to-blue-700 text-transparent bg-clip-text">
          Trending Footballers
        </h1>
        <p className="text-center text-gray-500 text-sm mb-6 sm:mb-8">Click on a player to see their latest news</p>
        {loading && (
          <ul className="space-y-3">
            {[...Array(10)].map((_, i) => (
              <div key={i} className="animate-pulse bg-white/50 h-16 rounded-xl"></div>
            ))}
          </ul>
        )}
        <AnimatePresence>
          <ul className="space-y-3">
            {footballers.map((footballer, index) => (
              <motion.li
                key={footballer.name}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ 
                  type: "spring",
                  stiffness: 400,
                  damping: 25
                }}
                onClick={() => handlePlayerClick(footballer.name)}
                className="group bg-white/80 rounded-xl p-4 flex items-center border border-white/40 hover:border-brand/20 hover:shadow-[0_8px_30px_rgb(0,0,0,0.12)] hover:-translate-y-0.5 cursor-pointer relative overflow-hidden"
                whileHover={{ 
                  scale: 1.02,
                  transition: { 
                    scale: {
                      type: "spring",
                      stiffness: 400,
                      damping: 25,
                      duration: 0.15
                    }
                  }
                }}
                whileTap={{ 
                  scale: 0.98,
                  transition: { 
                    duration: 0.1 
                  }
                }}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-brand/0 via-brand/0 to-brand/0 group-hover:from-brand/5 group-hover:via-brand/10 group-hover:to-brand/5"></div>
                
                <span className="text-transparent bg-clip-text bg-gradient-to-br from-brand to-blue-600 font-bold min-w-[1.5rem]">
                  {index + 1}
                </span>
                
                <div className="relative">
                  <div className="absolute inset-0 w-12 h-12 -m-0.5 bg-gradient-to-br from-brand to-blue-600 rounded-full group-hover:scale-110"></div>
                  <img 
                    src={footballer.player_photo} 
                    alt={footballer.name}
                    className="w-11 h-11 rounded-full object-cover mr-4 relative z-10"
                  />
                </div>

                <div className="flex-1">
                  <div className="flex flex-col">
                    <span className="text-base sm:text-lg font-semibold text-gray-800 group-hover:text-brand">
                      {footballer.name}
                    </span>
                    <div className="flex items-center text-sm text-gray-500 gap-2">
                      <img 
                        src={footballer.club_logo} 
                        alt={footballer.club}
                        className="w-5 h-5"
                      />
                      <img 
                        src={`https://flagcdn.com/256x192/${getCountryCode(footballer.nationality)}.png`}
                        alt={footballer.nationality}
                        className="h-4 w-auto"
                      />
                    </div>
                  </div>
                </div>

                <div className="relative flex items-center gap-2">
                  <motion.div 
                    className="text-sm font-mono bg-gradient-to-r from-brand/10 to-blue-600/10 px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg border border-brand/20 text-brand font-semibold group-hover:from-brand/20 group-hover:to-blue-600/20"
                    whileHover={{ 
                      scale: 1.05,
                      transition: { 
                        type: "spring",
                        stiffness: 400,
                        damping: 25,
                        duration: 0.15
                      }
                    }}
                    whileTap={{ scale: 1 }}
                  >
                    {footballer.searchInterest}
                  </motion.div>
                  <div className="opacity-0 group-hover:opacity-100 text-brand">
                    →
                  </div>
                </div>
              </motion.li>
            ))}
          </ul>
        </AnimatePresence>
        <motion.div 
          className="mt-6 sm:mt-8 text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <p className="text-sm text-gray-500">
            Last updated: {lastUpdate || 'Not available'}
          </p>
          <div className="flex items-center justify-center gap-2 mt-2">
            <div className="w-1.5 h-1.5 rounded-full bg-gradient-to-r from-brand to-blue-600 animate-pulse"></div>
            <p className="text-xs text-gray-500">
              Refreshes every 24 hours
            </p>
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}