import React, { useState, useRef, ReactNode, FC } from 'react'
import cn from 'classnames'
import FocusMonitor from './higher-order/FocusMonitor'

type PopoverProps = {
  children: (toggle: () => void) => ReactNode
  renderTitle: (toggle: () => void, isActive: boolean) => ReactNode
  className?: string
  contentClassName?: string
  isHover?: boolean
}

const Popover: FC<PopoverProps> = ({
  children,
  className,
  contentClassName,
  isHover,
  renderTitle,
}) => {
  const [isActive, setIsActive] = useState(false)
  const focusRef = useRef<any>(null)

  const _focusChanged = (active: boolean) => setIsActive(active)

  const toggle = () => {
    if (focusRef.current && typeof focusRef.current.toggle === 'function') {
      focusRef.current.toggle()
    }
  }

  const modalClassNames = cn(
    'inline-modal inline-modal--sm',
    { 'd-none': !isActive },
    contentClassName,
    className,
  )

  return (
    <FocusMonitor
      ref={focusRef}
      onFocusChanged={_focusChanged}
      isHover={isHover}
    >
      <div className={className}>
        {renderTitle(toggle, isActive)}
        <div>
          <div className={modalClassNames}>{children(toggle)}</div>
        </div>
      </div>
    </FocusMonitor>
  )
}

export default Popover
