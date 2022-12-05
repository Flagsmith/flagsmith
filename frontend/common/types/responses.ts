// eslint-disable-next-line @typescript-eslint/no-empty-interface
export type PagedResponse<T> = {
  count?: number
  next?: string
  previous?: string
  results: T[]
}
export type Res = {
  // END OF TYPES
}
