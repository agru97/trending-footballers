'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, ResponsiveContainer } from 'recharts'

interface PlayerNews {
  player_id: number
  player_name: string
  trending_score: number
  trend_summary: string
  interest_over_time?: {
    values: number[]
    dates: string[]
  }
}

interface PlayerDetailsProps {
  playerId: number
  onClose: () => void
  playerPhoto: string
  teamLogo: string
  countryFlag: string
  playerName: string
  rank: number
  interest_over_time?: {
    values: number[]
    dates: string[]
  }
}

export default function PlayerDetails({ 
  playerId, 
  onClose, 
  playerPhoto, 
  teamLogo, 
  countryFlag,
  playerName,
  rank,
  interest_over_time
}: PlayerDetailsProps) {
  const [news, setNews] = useState<PlayerNews | null>(null)
  const [loading, setLoading] = useState(true)
  const [showChart, setShowChart] = useState(false)

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const response = await fetch('/player_news.json')
        const data = await response.json()
        const playerNews = data.player_news.find((p: PlayerNews) => p.player_id === playerId)
        setNews(playerNews)
      } catch (error) {
        console.error('Error fetching news:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchNews()
  }, [playerId])

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ 
        type: 'spring', 
        damping: 30, 
        stiffness: 300,
        delay: 0.15
      }}
      onAnimationComplete={() => setShowChart(true)}
      className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.12)] p-6 w-[440px] border border-white/20"
    >
      <div className="relative">
        <button
          onClick={onClose}
          className="absolute -top-2 -right-2 bg-white hover:bg-brand rounded-full p-2 shadow-lg text-gray-500 hover:text-white transition-all duration-200"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {loading ? (
          <div className="flex items-center justify-center h-[460px]">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div>
          </div>
        ) : news ? (
          <div>
            <div className="flex items-center gap-5 mb-8">
              <div className="relative w-[76px] h-[76px]">
                <div className="absolute inset-0 bg-blue-600 rounded-full opacity-90"></div>
                <img
                  src={playerPhoto}
                  alt={playerName}
                  className="absolute top-1 left-1 w-[68px] h-[68px] rounded-full object-cover z-10"
                />
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-bold text-gray-800 mb-2">{playerName}</h2>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <img src={teamLogo} alt="Team" className="h-6 w-auto" />
                    <img src={countryFlag} alt="Country" className="h-5 w-auto shadow-sm rounded-[1px]" />
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="text-sm text-gray-500">Trending</div>
                    <div className="flex items-center gap-1">
                      <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-brand"></span>
                      </span>
                      <span className="text-brand font-semibold">#{rank}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="mb-6 bg-white/80 rounded-xl p-4 border border-white/40">
              <div className="h-24">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={interest_over_time?.values.map((value, index) => ({
                      value,
                      date: interest_over_time.dates[index]
                    }))
                    .sort((a, b) => new Date(a.date + 'Z').getTime() - new Date(b.date + 'Z').getTime())
                    .slice(12)
                    || []}
                    margin={{ top: 5, right: 5, bottom: 15, left: 15 }}
                  >
                    <defs>
                      <linearGradient id={`valueGradient-${playerId}`} x1="0" y1="1" x2="0" y2="0">
                        <stop offset="0%" stopColor="#0EA5E9" />
                        <stop offset="50%" stopColor="#8B5CF6" />
                        <stop offset="100%" stopColor="#EC4899" />
                      </linearGradient>
                    </defs>
                    <XAxis 
                      dataKey="date" 
                      interval={0}
                      tickCount={5}
                      ticks={interest_over_time?.dates
                        .filter((_, i) => i % 36 === 0)
                        .slice(1, 5)
                        || []}
                      tick={{ fontSize: 11, fill: '#6B7280' }}
                      tickFormatter={(value) => {
                        const date = new Date(value + 'Z');
                        let hours = date.getUTCHours();
                        if (date.getUTCDate() === 8) {
                          hours = hours + 24;
                        }
                        const ampm = (hours % 24) >= 12 ? 'PM' : 'AM';
                        hours = hours % 12;
                        hours = hours ? hours : 12;
                        return `${hours} ${ampm}`.padStart(5, ' ');
                      }}
                      axisLine={false}
                      tickLine={true}
                      tickSize={4}
                      dx={-5}
                      stroke="#E5E7EB"
                      minTickGap={30}
                    />
                    {showChart && (
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke={`url(#valueGradient-${playerId})`}
                        strokeWidth={2.5}
                        dot={false}
                        isAnimationActive={true}
                        animationDuration={800}
                        animationBegin={0}
                      />
                    )}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-white/80 rounded-xl p-6 border border-white/40">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">Latest Summary</h3>
              <p className="text-gray-600 leading-relaxed">{news.trend_summary}</p>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-[460px]">
            <p className="text-gray-500">No summary available</p>
          </div>
        )}
      </div>
    </motion.div>
  )
} 