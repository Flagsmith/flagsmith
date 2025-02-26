import React, {
  useState,
  useCallback,
  useRef,
  useEffect,
  useImperativeHandle,
  ReactElement,
  ForwardRefRenderFunction,
} from 'react'

export interface FocusMonitorProps {
  children: ReactElement
  isHover?: boolean
  onFocusChanged: (hasFocus: boolean) => void
}

export interface FocusMonitorHandles {
  toggle: () => void
  isActive: () => boolean
}

const FocusMonitor: ForwardRefRenderFunction<
  FocusMonitorHandles,
  FocusMonitorProps
> = ({ children, isHover, onFocusChanged }, ref) => {
  // State to track focus and last update timestamp
  const [state, setState] = useState<{ hasFocus: boolean; updated: number }>({
    hasFocus: false,
    updated: 0,
  })

  const containerRef = useRef<HTMLElement>(null)

  const focusChanged = useCallback(
    (hasFocus: boolean) => {
      setState((prev) => {
        if (hasFocus !== prev.hasFocus) {
          onFocusChanged(hasFocus)
          return { hasFocus, updated: Date.now() }
        }
        return prev
      })
    },
    [onFocusChanged],
  )

  const toggle = useCallback(() => {
    if (state.hasFocus && Date.now() - state.updated > 200) {
      focusChanged(!state.hasFocus)
    }
  }, [state, focusChanged])

  // Event handlers for hover mode
  const handleMouseOver = useCallback(() => {
    focusChanged(true)
  }, [focusChanged])
  const handleMouseLeave = useCallback(() => {
    focusChanged(false)
  }, [focusChanged])

  // Event handler for non-hover mode
  const handleClickDocument = useCallback(
    (e: MouseEvent) => {
      const node = containerRef.current
      // @ts-ignore
      if (node && (e.target === node || $(node).has(e.target).length)) {
        focusChanged(true)
      } else {
        focusChanged(false)
      }
    },
    [focusChanged],
  )

  // Attach event listeners after mount and remove on unmount
  useEffect(() => {
    const node = containerRef.current
    if (isHover) {
      if (node) {
        node.addEventListener('mouseover', handleMouseOver, false)
        node.addEventListener('mouseleave', handleMouseLeave, false)
      }
      return () => {
        if (node) {
          node.removeEventListener('mouseover', handleMouseOver, false)
          node.removeEventListener('mouseleave', handleMouseLeave, false)
        }
      }
    } else {
      window.addEventListener('mousedown', handleClickDocument, false)
      return () => {
        window.removeEventListener('mousedown', handleClickDocument, false)
      }
    }
  }, [isHover, handleMouseOver, handleMouseLeave, handleClickDocument])

  useImperativeHandle(
    ref,
    () => ({
      isActive: () => state.hasFocus,
      toggle,
    }),
    [toggle, state.hasFocus],
  )

  return React.isValidElement(children) ? (
    React.cloneElement(children, { ref: containerRef })
  ) : (
    <div ref={containerRef as any}>{children}</div>
  )
}

const ForwardedFocusMonitor = React.forwardRef(FocusMonitor)
export default ForwardedFocusMonitor
