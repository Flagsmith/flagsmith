import { RefObject, useEffect } from 'react'

/**
 * Keeps clicks inside `ref` from reaching the outside-click watchers, so a
 * subtree portalled elsewhere still counts as part of whatever opened it.
 *
 * Without this, an InlineModal holding a portalled menu closes on the very item
 * you picked, because the menu is not a DOM descendant of the modal. Native
 * listeners rather than React's onMouseUp, because those sit below document,
 * which is where useOutsideClick listens.
 */
const useContainClicks = (
  ref: RefObject<HTMLElement | null>,
  active = true,
) => {
  useEffect(() => {
    const node = ref.current
    if (!active || !node) return
    const stop = (e: Event) => e.stopPropagation()
    node.addEventListener('mouseup', stop)
    node.addEventListener('touchend', stop)
    return () => {
      node.removeEventListener('mouseup', stop)
      node.removeEventListener('touchend', stop)
    }
  }, [ref, active])
}

export default useContainClicks
