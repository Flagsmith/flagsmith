export const TRACKED_UTMS = [
  'utm_source',
  'utm_medium',
  'utm_campaign',
  'utm_content',
  'utm_term',
]

export type UtmsType = {
  [key in (typeof TRACKED_UTMS)[number]]: string
}
