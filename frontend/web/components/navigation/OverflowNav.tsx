import React, { FC, ReactNode, useEffect, useRef, useState } from 'react'
import InlineModal from 'components/InlineModal'
import { IonIcon } from '@ionic/react'
import { ellipsisHorizontal } from 'ionicons/icons'
import Button from 'components/base/forms/Button'
import classNames from 'classnames'
import { useHistory } from 'react-router-dom'
import { useVisibleCount } from 'common/hooks/useVisibleCount' // Assuming you place the hook here

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
  const history = useHistory()
  const { isMeasuring, visibleCount } = useVisibleCount({
    extraWidth: buttonWidth + 10,
    force,
    gap,
    itemCount: items.length,
    itemsContainerRef,
    outerContainerRef,
  })

  useEffect(() => {
    const unlisten = history.listen(() => {
      setOpen(false)
    })
    return () => unlisten()
  }, [history])

  const visible = items.slice(0, visibleCount)
  const overflow = items.slice(visibleCount)

  return (
    <div
      ref={outerContainerRef}
      className={classNames(
        'd-flex align-items-center w-100',
        { 'opacity-0': isMeasuring },
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
            onClick={() => setOpen(!open)}
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
