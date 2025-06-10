import React, {
  FC,
  ReactNode,
  useRef,
  useState,
  useLayoutEffect,
  useEffect,
} from 'react'
import InlineModal from './InlineModal'
import { IonIcon } from '@ionic/react'
import { ellipsisHorizontal } from 'ionicons/icons'
import Button from './base/forms/Button'
import classNames from 'classnames'
import { AsyncStorage } from 'polyfill-react-native'
import { useHistory } from 'react-router-dom'

type OverflowNavProps = {
  /** Nav items as children */
  children: ReactNode
  /** Classes for the outer flex container */
  containerClassName?: string
  /** Classes for the inner div that wraps the visible items */
  className?: string
  /** Bootstrap gap value (e.g. gap=3 for .gap-3) */
  gap?: number
}

const OverflowNav: FC<OverflowNavProps> = ({
  children: _children,
  className = '',
  containerClassName,
  gap,
}) => {
  const items = React.Children.toArray(
    (_children as React.ReactElement)?.props?.children || _children,
  )

  const outerContainerRef = useRef<HTMLDivElement>(null)
  const itemsContainerRef = useRef<HTMLDivElement>(null)

  const [open, setOpen] = useState(false)
  const [visibleCount, setVisibleCount] = useState(items.length)
  const [widths, setWidths] = useState<number[]>([])
  const history = useHistory()
  useEffect(() => {
    const updateLastViewed = () => {
      setOpen(false)
    }
    const unlisten = history.listen(updateLastViewed)
    return () => unlisten()
  }, [history])
  useLayoutEffect(() => {
    const itemsCont = itemsContainerRef.current
    if (!itemsCont || widths.length > 0) return

    const childEls = Array.from(itemsCont.children) as HTMLElement[]
    const w = childEls.map((el) => el.offsetWidth)
    setWidths(w)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items.length])

  useLayoutEffect(() => {
    const calculateVisibleCount = () => {
      const outerCont = outerContainerRef.current
      const itemsCont = itemsContainerRef.current
      if (!outerCont || !itemsCont || widths.length === 0) return

      const gapPx = gap * 4

      const sumWidths = (count: number) => {
        if (count === 0) return 0
        const totalWidths = widths
          .slice(0, count)
          .reduce((acc, w) => acc + w, 0)
        const totalGaps = (count - 1) * gapPx
        return totalWidths + totalGaps
      }

      // FIX: Use the outer container's width as the total available space.
      const containerWidth = outerCont.clientWidth

      if (sumWidths(widths.length) <= containerWidth) {
        if (visibleCount !== widths.length) {
          setVisibleCount(widths.length)
        }
        return
      }

      const overflowBtnWidth = 34 + 12 // + 12 due to the padding
      const reserve = overflowBtnWidth + gapPx
      const maxWidth = containerWidth - reserve

      let count = 0
      while (count < widths.length && sumWidths(count + 1) <= maxWidth) {
        count++
      }

      if (count !== visibleCount) {
        setVisibleCount(count)
      }
    }

    calculateVisibleCount()

    const ro = new ResizeObserver(calculateVisibleCount)
    if (outerContainerRef.current) ro.observe(outerContainerRef.current)
    window.addEventListener('resize', calculateVisibleCount)

    return () => {
      ro.disconnect()
      window.removeEventListener('resize', calculateVisibleCount)
    }
  }, [widths, visibleCount, gap, items.length])

  const visible = items.slice(0, visibleCount)
  const overflow = items.slice(visibleCount)

  return (
    <div
      ref={outerContainerRef} // Ref for the outer container
      className={classNames(
        'd-flex align-items-center',
        overflow.length > 0
          ? 'justify-content-between'
          : 'justify-content-start',
        containerClassName,
      )}
    >
      <div
        ref={itemsContainerRef} // Ref for the inner items wrapper
        className={classNames(
          className,
          gap ? `gap-${gap}` : undefined,
          'd-flex align-items-center',
          overflow.length > 0 ? 'flex-1' : '',
        )}
      >
        {visible.map((child, idx) => (
          <React.Fragment key={idx}>{child}</React.Fragment>
        ))}
      </div>

      {overflow.length > 0 && (
        <div className='nav-item dropdown position-relative'>
          <Button
            style={{ height: 30, width: 34 }}
            onClick={() => setOpen((o) => !o)}
            theme='secondary'
            className='d-flex align-items-center justify-content-center m-0 p-0'
          >
            <IonIcon className='fs-small' icon={ellipsisHorizontal} />
          </Button>
          <InlineModal
            relativeToParent
            hideClose
            isOpen={open}
            containerClassName='p-0'
            className='inline-modal-right'
            onClose={() => setOpen(false)}
          >
            <div className='d-flex flex-column no-wrap'>
              {overflow.map((child, idx) => (
                <React.Fragment key={idx}>{child}</React.Fragment>
              ))}
            </div>
          </InlineModal>
        </div>
      )}
    </div>
  )
}

export default OverflowNav
