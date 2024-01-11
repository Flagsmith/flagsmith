import { RefObject, useCallback, useEffect } from 'react'

const useOutsideClick = (ref: RefObject<HTMLElement>, handler: () => void) => {
  const handleClick = useCallback(
    (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        handler()
      }
    },
    [handler, ref],
  )

  useEffect(() => {
    document.addEventListener('click', handleClick)
    return () => document.removeEventListener('click', handleClick)
  }, [ref, handler, handleClick])
}

export default useOutsideClick
