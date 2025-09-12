import { useState } from 'react'

export default function useDebounce(func: any, delay: number) {
  const [timeout, saveTimeout] = useState<NodeJS.Timeout | null>(null)

  const debouncedFunc = function () {
    //eslint-disable-next-line
        const args = arguments
    if (timeout) {
      clearTimeout(timeout)
    }

    const newTimeout = setTimeout(function () {
      func(...args)
      if (newTimeout === timeout) {
        saveTimeout(null)
      }
    }, delay)

    saveTimeout(newTimeout)
  }

  return debouncedFunc as typeof func
}
/* Usage example:
const searchItems = useDebounce((search:string) => {
  doThing()
}, 500)
*/
