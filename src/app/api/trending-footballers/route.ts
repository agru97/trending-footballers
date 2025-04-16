import { NextResponse } from 'next/server'
import { promises as fs } from 'fs'
import path from 'path'

export async function GET() {
  try {
    // Read CSV file
    const csvPath = path.join(process.cwd(), 'public', 'trending_footballers.csv')
    const csvContent = await fs.readFile(csvPath, 'utf-8')
    
    // Read last update time
    const updatePath = path.join(process.cwd(), 'public', 'last_update.txt')
    const lastUpdate = await fs.readFile(updatePath, 'utf-8')
    
    // Parse CSV (skip header row)
    const lines = csvContent.split('\n').slice(1)
    const footballers = lines
      .filter(line => line.trim())
      .map(line => {
        const [name, trend_score, full_name, nationality, club, club_logo, player_photo] = 
          line.split(',').map(field => field.replace(/"/g, ''))
        
        return {
          name,
          searchInterest: parseFloat(trend_score),
          full_name,
          nationality,
          club,
          club_logo,
          player_photo
        }
      })

    return NextResponse.json({
      footballers,
      lastUpdate: new Date(lastUpdate).toLocaleString()
    })
  } catch (error) {
    console.error('Error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch trending footballers' },
      { status: 500 }
    )
  }
}