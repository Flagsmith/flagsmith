// Ids reach API calls unvalidated, since route params and store values arrive
// as strings. Number() also coerces non-ids ([] and true become numbers), so the
// input is narrowed first, and an id must be positive: these are serial keys.
export const isNumericId = (id: unknown): boolean =>
  (typeof id === 'number' || typeof id === 'string') &&
  Number.isInteger(Number(id)) &&
  Number(id) > 0
