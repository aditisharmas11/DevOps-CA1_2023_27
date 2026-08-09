import type { Trip } from '../types/trip'
import { Tokyo3Day } from './tokyo/3-day'
import { Tokyo5Day } from './tokyo/5-day'
import { Tokyo7Day } from './tokyo/7-day'
import { Dubai3Day } from './dubai/3-day'
import { Dubai5Day } from './dubai/5-day'
import { Dubai7Day } from './dubai/7-day'
import { Istanbul3Day } from './istanbul/3-day'
import { Istanbul5Day } from './istanbul/5-day'
import { Istanbul7Day } from './istanbul/7-day'

const tripDataMap: Record<string, Record<string, Trip>> = {
  Tokyo: {
    '3 Days': Tokyo3Day,
    '5 Days': Tokyo5Day,
    '7 Days': Tokyo7Day,
  },
  Dubai: {
    '3 Days': Dubai3Day,
    '5 Days': Dubai5Day,
    '7 Days': Dubai7Day,
  },
  Istanbul: {
    '3 Days': Istanbul3Day,
    '5 Days': Istanbul5Day,
    '7 Days': Istanbul7Day,
  },
}

export function getTripData(destination: string, duration: string): Trip | null {
  return tripDataMap[destination]?.[duration] ?? null
}
