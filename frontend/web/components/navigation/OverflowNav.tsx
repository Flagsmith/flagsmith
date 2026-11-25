import React, { FC, ReactNode, useRef } from 'react'
import { IonIcon } from '@ionic/react'
import { ellipsisHorizontal } from 'ionicons/icons'
import IconButton from 'components/base/IconButton'
import DropdownMenu, { DropdownMenuRow } from 'components/base/DropdownMenu'
import classNames from 'classnames'
import { useOverflowVisibleCount } from 'common/hooks/useOverflowVisibleCount'

type OverflowNavProps = {
  // Names the overflow button; each nav on a page needs its own
  label: string
  children: ReactNode
  containerClassName?: string
  className?: string
  gap?: number
  icon?: string
  force?: boolean
}
// Room for the overflow button, with some spare: nav icons load late and
// grow their items after they are measured
const OVERFLOW_BUTTON_WIDTH = 54

const OverflowNav: FC<OverflowNavProps> = ({
  children: _children,
  className = '',
  containerClassName,
  force,
  gap = 2,
  icon = ellipsisHorizontal,
  label,
}) => {
  const items = React.Children.toArray(
    (_children as React.ReactElement)?.props?.children || _children,
  )

  const outerContainerRef = useRef<HTMLDivElement>(null)
  const itemsContainerRef = useRef<HTMLDivElement>(null)
  const { isMeasuring, visibleCount } = useOverflowVisibleCount({
    extraWidth: OVERFLOW_BUTTON_WIDTH,
    force,
    itemCount: items.length,
    itemsContainerRef,
    outerContainerRef,
  })

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
        {/* Wrappers keep DOM children 1:1 with items so measured widths align,
            even when an item renders nothing or multiple elements */}
        {(isMeasuring ? items : visible).map((child, idx) => (
          <div
            key={idx}
            className={`d-flex align-items-center gap-${gap} flex-shrink-0`}
          >
            {child}
          </div>
        ))}
      </div>

      {overflow.length > 0 && !isMeasuring && (
        <DropdownMenu
          aria-label={label}
          trigger={
            <IconButton
              className='ms-2 flex-shrink-0'
              variant='secondary'
              size='small'
              aria-label={label}
            >
              <IonIcon className='fs-small' icon={icon} />
            </IconButton>
          }
        >
          {overflow.map((child, idx) => (
            <DropdownMenuRow key={idx}>{child}</DropdownMenuRow>
          ))}
        </DropdownMenu>
      )}
    </div>
  )
}

export default OverflowNav
