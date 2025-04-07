'use client'

import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import countryCodes from '../public/country-codes.json'
import { LineChart, Line, ResponsiveContainer } from 'recharts'
import PlayerDetails from './components/PlayerDetails'
import { Info, Coffee, CreditCard, Github, Search, Star, Trophy, Globe, ChartLine } from "lucide-react"

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
  const normalizedNationality = nationality.toLowerCase();
  
  // Special cases mapping
  const specialCases: { [key: string]: string } = {
    "côte d'ivoire": "ci",
    "ivory coast": "ci",
    "cote d'ivoire": "ci",
    "türkiye": "tr",
    "turkey": "tr",
    "usa": "us",
    "united states": "us",
    "england": "gb-eng",
    "republic of ireland": "ie",
    "korea republic": "kr",
    "south korea": "kr",
    "dr congo": "cd",
    "congo": "cg",
  };

  // Check special cases first
  if (specialCases[normalizedNationality]) {
    return specialCases[normalizedNationality];
  }

  // Regular country code lookup
  const countryCodesReverse = Object.entries(countryCodes)
    .reduce<{ [key: string]: string }>((acc, [code, name]) => {
      acc[name.toLowerCase()] = code;
      return acc;
    }, {});

  return countryCodesReverse[normalizedNationality] || normalizedNationality;
}

function Sparkline({ data, className }: { data: number[], className?: string }) {
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
          transform: translateZ(0);
        }

        .sparkline-path {
          stroke-dasharray: 200;
          stroke-dashoffset: 200;
          transition: stroke-dashoffset 1.5s ease-out;
          transform: translateZ(0);
          will-change: stroke-dashoffset;
        }
        
        .group:hover .sparkline-path {
          stroke-dashoffset: 0;
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
  const [selectedPlayer, setSelectedPlayer] = useState<Footballer | null>(null)

  const handlePlayerClick = (footballer: Footballer) => {
    // Only add delay for screens that show the plot (xs and larger, but not the smallest screen)
    if (window.innerWidth >= 375 && window.innerWidth < 768) {  // 375px is 'xs' breakpoint
      // First trigger the plot animation
      const listItem = document.querySelector(`[data-player-id="${footballer.player.id}"]`);
      if (listItem) {
        listItem.classList.add('group-hover');
        
        // Shorter delay to match the plot animation
        setTimeout(() => {
          setSelectedPlayer(footballer);
        }, 500); // Reduced from 1500ms to 800ms to match the plot animation duration
      }
    } else {
      // On smallest screens or larger screens, transition immediately
      setSelectedPlayer(footballer);
    }
  };

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
        
        // Format the date string directly from the timestamp
        const timestamp = data.updated_at // "2025-01-05T12:00:07.010932Z"
        const date = new Date(timestamp)
        const formattedDate = `${date.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric'
        })} at ${date.toLocaleTimeString('en-US', {
          hour: 'numeric',
          minute: 'numeric',
          hour12: true
        })}`
        setLastUpdate(formattedDate)

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
    <div className="relative">
      {/* Rankings Section */}
      <section id="rankings" className="snap-section bg-[#4D96FF]">
        <div className="min-h-screen w-full flex items-center justify-center p-4">
          <div className="relative w-[320px] xs:w-[375px] sm:w-[410px]">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ 
                opacity: 1, 
                scale: 1,
                x: selectedPlayer ? '-110%' : 0,
              }}
              transition={{ 
                duration: 0.3,
                ease: "easeInOut"
              }}
              className="relative bg-white/95 backdrop-blur-xl rounded-lg shadow-[0_8px_30px_rgb(0,0,0,0.12)] p-6 w-[320px] xs:w-[375px] sm:w-[410px] border border-white/20"
            >
              <motion.div
                className="absolute -top-4 left-0 right-0 mx-auto w-fit"
                initial={{ y: -20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
              >
                <div className="text-center mt-8">
                  <h1 className="text-3xl font-bold text-brand">Trending Footballers</h1>
                  <p className="text-gray-500 text-sm mt-2">Based on global search interest in the last 24 hours</p>
                </div>
              </motion.div>
              <div className="mt-24">
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
                        data-player-id={footballer.player.id}
                        initial={{ opacity: 0, scale: 0.97 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.97 }}
                        transition={{ 
                          type: "spring",
                          stiffness: 400,
                          damping: 30
                        }}
                        onClick={() => handlePlayerClick(footballer)}
                        className={`
                          group bg-white/80 rounded-xl p-4 flex items-center border 
                          transition-all duration-300 touch-manipulation relative overflow-hidden
                          ${selectedPlayer?.player.id === footballer.player.id 
                            ? 'border-brand shadow-[0_0_0_2px_#4D96FF] bg-brand/5 hover:border-brand hover:shadow-[0_0_0_2px_#4D96FF]' 
                            : 'border-white/40 hover:border-brand/20 active:border-brand/40 hover:shadow-[0_8px_30px_rgb(0,0,0,0.12)] hover:-translate-y-0.5 active:translate-y-0'
                          }
                          cursor-pointer
                        `}
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
                        <span className="text-transparent bg-clip-text bg-gradient-to-br from-brand to-blue-600 font-bold min-w-[1.5rem] transition-transform duration-200 group-hover:scale-110">
                          {footballer.rank}
                        </span>
                        
                        <div className="relative">
                          <div className="absolute inset-0 w-12 h-12 -m-0.5 bg-gradient-to-br from-brand to-blue-600 rounded-full group-hover:scale-110"></div>
                          <img 
                            src={footballer.player.photo} 
                            alt={footballer.player.name}
                            className="w-11 h-11 rounded-full object-cover mr-4 relative z-10"
                          />
                        </div>

                        <div className="flex-1 min-w-0">
                          <div className="flex flex-col">
                            <span className="text-lg font-semibold text-gray-800 group-hover:text-brand truncate">
                              {footballer.player.name}
                            </span>
                            <div className="flex items-center text-sm text-gray-500 gap-2 min-w-0">
                              <img 
                                src={footballer.statistics[0].team.logo} 
                                alt={footballer.statistics[0].team.name}
                                className="h-5 w-auto flex-shrink-0 object-contain"
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
                            <div className="hidden xs:block w-24 h-8 relative" style={{ transform: 'translate3d(0,0,0)' }}>
                              <div className="absolute inset-0">
                                <Sparkline 
                                  data={footballer.interest_over_time.values}
                                  className="sparkline-path"
                                />
                              </div>
                            </div>
                          )}
                          <div className="hidden md:block opacity-0 group-hover:opacity-100 text-brand transition-opacity duration-200">
                            →
                          </div>
                        </div>
                      </motion.li>
                    ))}
                  </ul>
                </AnimatePresence>
              </div>
              <motion.div 
                className="mt-4 sm:mt-8 text-center"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
              >
                <p className="text-sm text-gray-500">
                  Last updated: {lastUpdate}
                </p>
                <div className="flex items-center justify-center gap-2 mt-2 opacity-75 hover:opacity-100 transition-opacity duration-200">
                  <div className="w-1.5 h-1.5 rounded-full bg-gradient-to-r from-brand to-blue-600 animate-pulse"></div>
                  <p className="text-xs text-gray-500">
                    Refreshes every 12 hours
                  </p>
                </div>
              </motion.div>
            </motion.div>

            <AnimatePresence mode="wait">
              {selectedPlayer && (
                <motion.div
                  key={`player-${selectedPlayer.player.id}`}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ 
                    opacity: 0, 
                    scale: 0.95,
                    transition: {
                      duration: 0.15
                    }
                  }}
                  transition={{ 
                    type: 'spring', 
                    damping: 30, 
                    stiffness: 300,
                    delay: 0.15
                  }}
                  className="absolute top-0 left-0"
                >
                  <PlayerDetails
                    playerId={selectedPlayer.player.id}
                    onClose={() => setSelectedPlayer(null)}
                    playerPhoto={selectedPlayer.player.photo}
                    teamLogo={selectedPlayer.statistics[0].team.logo}
                    countryFlag={`https://flagcdn.com/256x192/${getCountryCode(selectedPlayer.player.nationality)}.png`}
                    playerName={selectedPlayer.player.name}
                    rank={selectedPlayer.rank}
                    interest_over_time={selectedPlayer.interest_over_time}
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </section>

      {/* Search Section */}
      <section id="search" className="snap-section bg-brand">
        <div className="min-h-screen w-full flex items-center justify-center p-4">
          <div className="w-[320px] xs:w-[375px] sm:w-[410px] bg-white/95 backdrop-blur-xl rounded-lg shadow-[0_8px_30px_rgb(0,0,0,0.12)] p-6 border border-white/20">
            <div className="text-center space-y-4">
              <div className="mx-auto w-16 h-16 bg-blue-100 rounded-lg flex items-center justify-center">
                <Search className="w-8 h-8 text-brand" />
              </div>
              <h1 className="text-2xl font-bold text-gray-800">Player Search</h1>
              <p className="text-gray-500">
                Coming soon! Search for any football player and track their trending status.
              </p>
              <div className="mt-8 space-y-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="font-medium text-gray-700">Planned Features:</h3>
                  <ul className="mt-2 space-y-2 text-sm text-gray-600">
                    <li>• Real-time player search</li>
                    <li>• Historical trend data</li>
                    <li>• Advanced filters by league, team, and position</li>
                    <li>• Player comparison tools</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="snap-section bg-brand">
        <div className="min-h-screen w-full flex items-center justify-center p-4">
          <div className="w-[320px] xs:w-[375px] sm:w-[410px] bg-white/95 backdrop-blur-xl rounded-lg shadow-[0_8px_30px_rgb(0,0,0,0.12)] p-6 border border-white/20">
            <div className="text-center space-y-4">
              <div className="mx-auto w-16 h-16 bg-blue-100 rounded-lg flex items-center justify-center">
                <Star className="w-8 h-8 text-brand" />
              </div>
              <h1 className="text-2xl font-bold text-gray-800">Features</h1>
              <p className="text-gray-500">
                We're working on exciting new features to enhance your experience!
              </p>
              <div className="mt-8 space-y-6">
                <div className="grid grid-cols-1 gap-4">
                  <div className="bg-gray-50 p-4 rounded-lg flex items-start space-x-4">
                    <div className="bg-blue-100 p-2 rounded-lg">
                      <Trophy className="w-6 h-6 text-brand" />
                    </div>
                    <div className="text-left">
                      <h3 className="font-medium text-gray-700">Player Rankings</h3>
                      <p className="text-sm text-gray-500 mt-1">
                        Track your favorite players' performance and trending status
                      </p>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 p-4 rounded-lg flex items-start space-x-4">
                    <div className="bg-blue-100 p-2 rounded-lg">
                      <Globe className="w-6 h-6 text-brand" />
                    </div>
                    <div className="text-left">
                      <h3 className="font-medium text-gray-700">Global Coverage</h3>
                      <p className="text-sm text-gray-500 mt-1">
                        Expanding to more leagues and competitions worldwide
                      </p>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 p-4 rounded-lg flex items-start space-x-4">
                    <div className="bg-blue-100 p-2 rounded-lg">
                      <ChartLine className="w-6 h-6 text-brand" />
                    </div>
                    <div className="text-left">
                      <h3 className="font-medium text-gray-700">Advanced Analytics</h3>
                      <p className="text-sm text-gray-500 mt-1">
                        Detailed statistics and trend analysis coming soon
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Info/About Section */}
      <section id="about" className="snap-section bg-brand">
        <div className="min-h-screen w-full flex items-center justify-center p-4">
          <div className="w-[320px] xs:w-[375px] sm:w-[410px] bg-white/95 backdrop-blur-xl rounded-lg shadow-[0_8px_30px_rgb(0,0,0,0.12)] p-6 border border-white/20">
            <div className="text-center space-y-4">
              <div className="mx-auto w-16 h-16 bg-blue-100 rounded-lg flex items-center justify-center">
                <Info className="w-8 h-8 text-brand" />
              </div>
              <h1 className="text-2xl font-bold text-gray-800">About & Support</h1>
              <p className="text-gray-500">
                Trending Footballers tracks real-time popularity and trending status of football players worldwide.
              </p>

              <div className="mt-8 space-y-6">
                <div className="bg-gray-50 p-6 rounded-lg text-left">
                  <h3 className="font-medium text-gray-700 mb-4">Support Our Platform</h3>
                  <p className="text-sm text-gray-500 mb-6">
                    Help us maintain and improve Trending Footballers! Your support helps cover our API costs,
                    server expenses, and enables us to add more features.
                  </p>
                  
                  <div className="space-y-3">
                    <a
                      href="https://www.buymeacoffee.com/YOUR_USERNAME"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-center gap-2 w-full px-4 py-2 bg-[#FFDD00] text-gray-900 rounded-lg hover:bg-[#FFDD00]/90 transition-colors"
                    >
                      <Coffee className="w-5 h-5" />
                      <span className="font-medium">Buy us a coffee</span>
                    </a>
                    
                    <a
                      href="https://www.paypal.com/donate/?hosted_button_id=YOUR_BUTTON_ID"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-center gap-2 w-full px-4 py-2 bg-[#0070BA] text-white rounded-lg hover:bg-[#003087] transition-colors"
                    >
                      <CreditCard className="w-5 h-5" />
                      <span className="font-medium">Donate with PayPal</span>
                    </a>

                    <a
                      href="https://github.com/YOUR_USERNAME/trending-footballers"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-center gap-2 w-full px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors"
                    >
                      <Github className="w-5 h-5" />
                      <span className="font-medium">Star on GitHub</span>
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}