import { useState } from 'react'

type ConditionCache = Record<number, Record<string, string>>

const getCacheKey = (operator: string, property: string): string => {
  return `${operator}|${property}`
}

/**
 * Custom hook to manage caching of condition values across operator/property changes.
 *
 * This hook preserves user input when switching between different operator/property
 * combinations, allowing users to explore options without losing their data.
 *
 * @example
 * const { cacheValue, getCachedValue } = useConditionCache()
 *
 * // Before changing operator, cache the current value
 * cacheValue(0, 'IN', '$.environment.name', '["dev","prod"]')
 *
 * // When switching to new operator, get cached value or empty
 * const value = getCachedValue(0, 'EQUAL', '$.environment.name') // Returns '' (not cached yet)
 */
export const useConditionCache = () => {
  const [cache, setCache] = useState<ConditionCache>({})

  const cacheValue = (
    conditionIndex: number,
    operator: string,
    property: string,
    value: string | number | boolean | null,
  ): void => {
    if (value === null || value === undefined) return

    const cacheKey = getCacheKey(operator, property)
    setCache((prev) => ({
      ...prev,
      [conditionIndex]: {
        ...prev[conditionIndex],
        [cacheKey]: String(value),
      },
    }))
  }

  const getCachedValue = (
    conditionIndex: number,
    operator: string,
    property: string,
  ): string => {
    const cacheKey = getCacheKey(operator, property)
    return cache[conditionIndex]?.[cacheKey] ?? ''
  }

  return {
    cacheValue,
    getCachedValue,
  }
}
