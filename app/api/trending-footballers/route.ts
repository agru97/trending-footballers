import { NextResponse } from 'next/server'
import fs from 'fs/promises'
import path from 'path'

const CSV_FILE = path.join(process.cwd(), 'public', 'trending_footballers.csv')
const TIMESTAMP_FILE = path.join(process.cwd(), 'public', 'last_update.txt')

export async function GET() {
  try {
    const csvData = await fs.readFile(CSV_FILE, 'utf-8')
    let lastUpdate
    
    try {
      lastUpdate = await fs.readFile(TIMESTAMP_FILE, 'utf-8')
    } catch (error) {
      // If timestamp file doesn't exist or is empty, use current time
      lastUpdate = new Date().toISOString()
    }
    
    console.log('Raw lastUpdate:', lastUpdate)
    console.log('Trimmed lastUpdate:', lastUpdate.trim())
    
    const footballers = csvData.trim().split('\n').map(line => {
      const [name, searchInterest] = line.split(',')
      return { name, searchInterest: Number(searchInterest) }
    })

    try {
      const parsedDate = new Date(lastUpdate.trim() || new Date().toISOString())
      return NextResponse.json({ 
        footballers,
        lastUpdate: parsedDate.toLocaleString('en-US', {
          dateStyle: 'medium',
          timeStyle: 'short'
        })
      })
    } catch (dateError) {
      console.error('Date parsing error:', dateError, 'Raw date string:', lastUpdate)
      return NextResponse.json({ 
        footballers,
        lastUpdate: new Date().toLocaleString('en-US', {
          dateStyle: 'medium',
          timeStyle: 'short'
        })
      })
    }
  } catch (error) {
    console.error('Error reading files:', error)
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 })
  }
}