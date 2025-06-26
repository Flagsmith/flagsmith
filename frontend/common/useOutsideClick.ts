import { RefObject, useEffect } from 'react'

const useOutsideClick = (
  ref: RefObject<HTMLElement>,
  handler: (event: MouseEvent | TouchEvent) => void,
) => {
  useEffect(() => {
    const listener = (event: MouseEvent | TouchEvent) => {
      if (!ref.current || ref.current.contains(event.target as Node)) {
        return
      }
      setTimeout(() => {
        //ensures that other handlers get hit first
        handler(event)
      }, 100)
    }

    document.addEventListener('mouseup', listener)
    document.addEventListener('touchend', listener)

    return () => {
      document.removeEventListener('mouseup', listener)
      document.removeEventListener('touchend', listener)
    }
  }, [ref, handler])
}

export default useOutsideClick
