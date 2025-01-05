'use client'

import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import countryCodes from '../public/country-codes.json'
import { LineChart, Line, ResponsiveContainer } from 'recharts'

interface Footballer {
  rank: number
  trending_score: number
  player: {
    id: number
    name: string
    firstname: string
    lastname: string
    nationality: string
    photo: string
  }
  statistics: [{
    team: {
      id: number
      name: string
      logo: string
    }
  }]
  interest_over_time?: {
    values: number[]
    dates: string[]
  }
}

interface TrendingData {
  updated_at: string
  players: Footballer[]
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

function Sparkline({ data }: { data: number[] }) {
  const smoothData = data.reduce((acc: number[], val: number, i: number) => {
    if (i < 12) return acc;
    const windowSum = data.slice(i - 12, i).reduce((sum, v) => sum + v, 0);
    const avg = windowSum / 12;
    if (i % 6 === 0) {
      acc.push(avg);
    }
    return acc;
  }, []);

  const chartData = smoothData.map((value) => ({ value }));
  const maxValue = Math.max(...smoothData);

  return (
    <div className="w-full h-full" style={{ transform: 'translate3d(0,0,0)' }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <defs>
            <linearGradient id="valueGradient" x1="0" y1="1" x2="0" y2="0">
              <stop offset="0%" stopColor="#0EA5E9" />
              <stop offset="50%" stopColor="#8B5CF6" />
              <stop offset="100%" stopColor="#EC4899" />
            </linearGradient>
          </defs>
          <Line
            type="monotone"
            dataKey="value"
            stroke="url(#valueGradient)"
            strokeWidth={2.5}
            dot={false}
            isAnimationActive={false}
            className="sparkline-path-bg"
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="url(#valueGradient)"
            strokeWidth={3.5}
            dot={false}
            isAnimationActive={false}
            className="sparkline-path"
          />
        </LineChart>
      </ResponsiveContainer>

      <style jsx global>{`
        .sparkline-path-bg {
          opacity: 0.5;
          filter: drop-shadow(0 0 2px rgba(14, 165, 233, 0.3));
          transform: translateZ(0);
        }

        .sparkline-path {
          stroke-dasharray: 200;
          stroke-dashoffset: 200;
          filter: drop-shadow(0 0 3px rgba(14, 165, 233, 0.5));
          transition: stroke-dashoffset 1.5s ease-out;
          transform: translateZ(0);
          will-change: stroke-dashoffset;
        }
        
        .group:hover .sparkline-path {
          stroke-dashoffset: 0;
          filter: drop-shadow(0 0 4px rgba(14, 165, 233, 0.7));
        }

        /* Reset animation when not hovering */
        .group:not(:hover) .sparkline-path {
          stroke-dashoffset: 200;
          transition: stroke-dashoffset 0.3s ease-out;
        }
      `}</style>
    </div>
  )
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
        setLoading(true)
        const response = await fetch('/trending_footballers.json')
        if (!response.ok) {
          throw new Error('Network response was not ok')
        }
        const data: TrendingData = await response.json()
        setFootballers(data.players)
        setLastUpdate(new Date(data.updated_at).toLocaleString())
      } catch (err: any) {
        setError(err.message || 'An error occurred')
        console.error('Fetch error:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchFootballers()
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

  if (!footballers || footballers.length === 0) {
    return (
      <div className="min-h-screen bg-[#4D96FF] flex items-center justify-center p-4">
        <div className="text-center text-white">
          <div className="text-xl font-medium">No data available</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen w-full bg-brand flex items-center justify-center p-8">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="relative bg-white/95 backdrop-blur-xl rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.12)] p-8 w-full max-w-md border border-white/20"
      >
        <motion.div 
          className="absolute -top-4 left-0 right-0 mx-auto w-fit"
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <div className="bg-gradient-to-r from-brand to-blue-600 text-white text-sm py-2 px-4 rounded-full shadow-lg flex items-center gap-2 animate-pulse-slow">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-white"></span>
            </span>
            Live Rankings
          </div>
        </motion.div>
        <h1 className="text-4xl font-bold text-center mb-2 bg-gradient-to-r from-brand to-blue-700 text-transparent bg-clip-text">
          Trending Footballers
        </h1>
        <p className="text-center text-gray-500 text-sm mb-8">Based on Search Interest in the last 24 hours</p>
        {loading && (
          <ul className="space-y-3">
            {[...Array(10)].map((_, i) => (
              <div key={i} className="animate-pulse bg-white/50 h-16 rounded-xl"></div>
            ))}
          </ul>
        )}
        <AnimatePresence>
          <ul className="space-y-3">
            {footballers.map((footballer) => (
              <motion.li
                key={footballer.player.name}
                initial={{ opacity: 0, scale: 0.97 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.97 }}
                transition={{ 
                  type: "spring",
                  stiffness: 400,
                  damping: 30
                }}
                onClick={() => handlePlayerClick(footballer.player.name)}
                className="group bg-white/80 rounded-xl p-4 flex items-center border border-white/40 hover:border-brand/20 active:border-brand/40 hover:shadow-[0_8px_30px_rgb(0,0,0,0.12)] hover:-translate-y-0.5 active:translate-y-0 cursor-pointer relative overflow-hidden transition-all duration-300 touch-manipulation"
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
                <div className="absolute inset-0 bg-gradient-to-r from-brand/0 via-brand/0 to-brand/0 group-hover:from-brand/5 group-hover:via-brand/10 group-hover:to-brand/5 transition-colors duration-500"></div>
                
                <span className="text-transparent bg-clip-text bg-gradient-to-br from-brand to-blue-600 font-bold min-w-[1.5rem] transition-transform duration-200 group-hover:scale-110">
                  {footballer.rank}
                </span>
                
                <div className="relative">
                  <div className="absolute inset-0 w-10 sm:w-12 h-10 sm:h-12 -m-0.5 bg-gradient-to-br from-brand to-blue-600 rounded-full group-hover:scale-110"></div>
                  <img 
                    src={footballer.player.photo} 
                    alt={footballer.player.name}
                    className="w-9 sm:w-11 h-9 sm:h-11 rounded-full object-cover mr-3 sm:mr-4 relative z-10"
                  />
                </div>

                <div className="flex-1">
                  <div className="flex flex-col">
                    <span className="text-lg font-semibold text-gray-800 group-hover:text-brand truncate">
                      {footballer.player.name}
                    </span>
                    <div className="flex items-center text-sm text-gray-500 gap-2 min-w-0">
                      <img 
                        src={footballer.statistics[0].team.logo} 
                        alt={footballer.statistics[0].team.name}
                        className="w-5 h-5 flex-shrink-0"
                        loading="lazy"
                        onError={(e) => {
                          e.currentTarget.style.opacity = '0.5';
                        }}
                      />
                      <img 
                        src={`https://flagcdn.com/256x192/${getCountryCode(footballer.player.nationality)}.png`}
                        alt={footballer.player.nationality}
                        className="h-4 w-auto flex-shrink-0"
                      />
                    </div>
                  </div>
                </div>

                <div className="relative flex items-center gap-2">
                  {footballer.interest_over_time && (
                    <div className="w-24 h-8 relative" style={{ transform: 'translate3d(0,0,0)' }}>
                      <div className="absolute inset-0">
                        <Sparkline data={footballer.interest_over_time.values} />
                      </div>
                    </div>
                  )}
                  <div className="opacity-0 group-hover:opacity-100 text-brand transition-opacity duration-200">
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
            Last updated: {new Date(lastUpdate).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              hour: 'numeric',
              minute: 'numeric'
            })}
          </p>
          <div className="flex items-center justify-center gap-2 mt-2 opacity-75 hover:opacity-100 transition-opacity duration-200">
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