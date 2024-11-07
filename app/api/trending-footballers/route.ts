import { NextResponse } from 'next/server'
import fs from 'fs/promises'
import path from 'path'

const CSV_FILE = path.join(process.cwd(), 'public', 'trending_footballers.csv')

export async function GET() {
  try {
    const csvData = await fs.readFile(CSV_FILE, 'utf-8')
    const footballers = csvData.trim().split('\n').map(line => {
      const [name, searchInterest] = line.split(',')
      return { name, searchInterest: Number(searchInterest) }
    })

    return NextResponse.json(footballers)
  } catch (error) {
    console.error('Error reading CSV file:', error)
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 })
  }
}