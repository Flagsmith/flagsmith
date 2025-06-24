import React, {
  FC,
  ReactNode,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from 'react'
import InlineModal from 'components/InlineModal'
import { IonIcon } from '@ionic/react'
import { ellipsisHorizontal } from 'ionicons/icons'
import Button from 'components/base/forms/Button'
import classNames from 'classnames'
import { useHistory } from 'react-router-dom'

type OverflowNavProps = {
  children: ReactNode
  containerClassName?: string
  className?: string
  gap?: number
  icon?: string
  force?: boolean
}
const buttonWidth = 34
const OverflowNav: FC<OverflowNavProps> = ({
  children: _children,
  className = '',
  containerClassName,
  force,
  gap = 2,
  icon = ellipsisHorizontal,
}) => {
  const items = React.Children.toArray(
    (_children as React.ReactElement)?.props?.children || _children,
  )

  const outerContainerRef = useRef<HTMLDivElement>(null)
  const itemsContainerRef = useRef<HTMLDivElement>(null)

  const [open, setOpen] = useState(false)
  const [visibleCount, setVisibleCount] = useState(force ? 0 : items.length)
  const [widths, setWidths] = useState<number[]>([])
  const history = useHistory()
  useEffect(() => {
    const unlisten = history.listen(() => {
      setOpen(false)
    })
    return () => unlisten()
  }, [history])

  useEffect(() => {
    if (force) {
      return
    }
    setWidths([])
    setVisibleCount(items.length)
  }, [_children, force])

  useLayoutEffect(() => {
    if (force) {
      return
    }
    const itemsCont = itemsContainerRef.current
    if (!itemsCont || widths.length > 0 || items.length === 0) {
      return
    }

    const childEls = Array.from(itemsCont.children) as HTMLElement[]
    const newWidths = childEls.map((el) => el.offsetWidth)
    setWidths(newWidths)
  }, [items.length, force, widths]) // It runs when items change and widths have been reset.

  useLayoutEffect(() => {
    if (force) {
      return
    }
    const calculate = () => {
      const outerCont = outerContainerRef.current
      if (!outerCont || widths.length === 0) {
        return
      }

      const gapPx = gap * 4 // Assuming a spacer unit of 4px. Adjust if needed.

      const sumWidths = (count: number) => {
        if (count === 0) return 0
        const totalWidths = widths
          .slice(0, count)
          .reduce((acc, w) => acc + w, 0)
        const totalGaps = (count > 1 ? count - 1 : 0) * gapPx
        return totalWidths + totalGaps
      }

      const containerWidth = outerCont.clientWidth

      if (sumWidths(widths.length) <= containerWidth) {
        setVisibleCount(widths.length)
        return
      }

      const reserve = buttonWidth + gapPx
      const maxWidth = containerWidth - reserve

      let count = 0
      while (count < widths.length && sumWidths(count + 1) <= maxWidth) {
        count++
      }
      setVisibleCount(count)
    }

    calculate()

    const ro = new ResizeObserver(calculate)
    if (outerContainerRef.current) {
      ro.observe(outerContainerRef.current)
    }
    return () => ro.disconnect()
  }, [widths, force, gap, items.length]) // Re-calculate when widths or container size changes.

  const visible = items.slice(0, visibleCount)
  const overflow = items.slice(visibleCount)
  const isMeasuring = force ? false : widths.length === 0 && items.length > 0

  return (
    <div
      ref={outerContainerRef}
      style={{ visibility: isMeasuring ? 'hidden' : 'visible' }} // Hide container while measuring
      className={classNames(
        'd-flex align-items-center w-100',
        overflow.length > 0 && !isMeasuring
          ? 'justify-content-between'
          : 'justify-content-start',
        containerClassName,
      )}
    >
      <div
        ref={itemsContainerRef}
        className={classNames(
          className,
          `gap-${gap}`,
          'd-flex align-items-center',
        )}
      >
        {(isMeasuring ? items : visible).map((child, idx) => (
          <React.Fragment key={idx}>{child}</React.Fragment>
        ))}
      </div>

      {overflow.length > 0 && !isMeasuring && (
        <div className='ms-2 nav-item dropdown position-relative flex-shrink-0'>
          <Button
            style={{ height: buttonWidth, width: buttonWidth }}
            onClick={(e) => {
              setOpen(!open)
            }}
            theme='secondary'
            className='d-flex align-items-center justify-content-center m-0 p-0'
          >
            <IonIcon className='fs-small' icon={icon} />
          </Button>
          <InlineModal
            relativeToParent
            hideClose
            isOpen={open}
            containerClassName='p-0'
            className='inline-modal-right'
            onClose={() => {
              setOpen(false)
            }}
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
