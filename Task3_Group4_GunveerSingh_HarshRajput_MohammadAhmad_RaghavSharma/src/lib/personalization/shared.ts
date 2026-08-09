import type { LocalTip, Trip } from '../../types/trip'

export function cloneTrip(baseTrip: Trip): Trip {
  return JSON.parse(JSON.stringify(baseTrip)) as Trip
}

export function createId(prefix: string): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return `${prefix}-${crypto.randomUUID().slice(0, 8)}`
  }

  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`
}

export function appendNote(note: string | undefined, addition: string): string {
  if (!note) {
    return addition
  }

  if (note.includes(addition)) {
    return note
  }

  return `${note} ${addition}`
}

export function prependTips(existing: LocalTip[], additions: Array<{ title: string; summary: string; category: LocalTip['category']; priority: LocalTip['priority'] }>): LocalTip[] {
  const generated = additions.map((tip) => ({
    id: createId('tip-personalized'),
    title: tip.title,
    summary: tip.summary,
    category: tip.category,
    priority: tip.priority,
  }))

  return [...generated, ...existing]
}
