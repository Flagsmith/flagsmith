import { useState } from 'react'

export default function useThrottle(func: any, delay: number) {
    const [timeout, saveTimeout] = useState<NodeJS.Timeout | null>(null)

    const throttledFunc = function () {
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

    return throttledFunc as typeof func
}
/* Usage example:
const searchItems =  useThrottle((search:string) => {
  doThing()
}, 100)
*/
