export type EventOption = { label: string; value: string }

export const buildEventOptions = (events?: string[]): EventOption[] =>
  (events ?? []).map((event) => ({ label: event, value: event }))

export const isUnknownEvent = (value: string, events?: string[]): boolean =>
  !!value && Array.isArray(events) && !events.includes(value)
