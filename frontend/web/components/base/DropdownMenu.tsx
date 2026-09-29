import React, { useEffect, useLayoutEffect, useRef, useState } from 'react'
import Icon, { IconName } from 'components/icons/Icon'
import classNames from 'classnames'
import useOutsideClick from 'common/useOutsideClick'
import { createPortal } from 'react-dom'
import { calculateListPosition } from 'common/utils/calculateListPosition'

type MenuItem = {
  icon?: IconName
  label: string | React.ReactNode
  onClick: (e: React.MouseEvent<HTMLDivElement>) => void
  disabled?: boolean
  tooltip?: string
  dataTest?: string
  className?: string
}

type DropdownMenuProps = {
  items: MenuItem[]
  className?: string
  buttonClassName?: string
  iconClassName?: string
  iconWidth?: number
  iconFill?: string
}

const DropdownMenu: React.FC<DropdownMenuProps> = ({
  buttonClassName,
  className,
  iconClassName,
  iconFill = '#9DA4AE',
  iconWidth = 18,
  items,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const btnRef = useRef<HTMLButtonElement>(null)
  const dropDownRef = useRef<HTMLDivElement>(null)
  useOutsideClick(dropDownRef, () => setIsOpen(false))

  // The menu is portalled to the body, so anything else watching for a click
  // outside itself counts a click in here as one: an InlineModal holding this
  // menu would close on the very item you picked. The menu belongs to its
  // trigger wherever it is drawn, so the event stops at its root. Native
  // rather than React's onMouseUp, because those listeners sit below document,
  // which is where the outside-click watchers are.
  useEffect(() => {
    const node = dropDownRef.current
    if (!isOpen || !node) return
    const stop = (e: Event) => e.stopPropagation()
    node.addEventListener('mouseup', stop)
    node.addEventListener('touchend', stop)
    return () => {
      node.removeEventListener('mouseup', stop)
      node.removeEventListener('touchend', stop)
    }
  }, [isOpen])

  useLayoutEffect(() => {
    if (!isOpen || !dropDownRef.current || !btnRef.current) return
    const listPosition = calculateListPosition(
      btnRef.current,
      dropDownRef.current,
    )
    dropDownRef.current.style.top = `${listPosition.top}px`
    dropDownRef.current.style.left = `${listPosition.left}px`
  }, [btnRef, isOpen, dropDownRef])

  return (
    <div className={classNames('feature-action', className)} tabIndex={-1}>
      <button
        className={classNames('btn btn-link p-0', buttonClassName)}
        onClick={(e) => {
          e.stopPropagation()
          setIsOpen(!isOpen)
        }}
        ref={btnRef}
      >
        <Icon
          name='more-vertical'
          width={iconWidth}
          fill={iconFill}
          className={iconClassName}
        />
      </button>

      {isOpen &&
        createPortal(
          <div ref={dropDownRef} className='feature-action__list'>
            {items.map((item, index) => (
              <Tooltip
                key={index}
                title={
                  <div
                    className={classNames(
                      'feature-action__item',
                      item.className,
                      {
                        'feature-action__item_disabled': item.disabled,
                      },
                    )}
                    data-test={item.dataTest}
                    onClick={(e) => {
                      e.stopPropagation()
                      if (!item.disabled) {
                        item.onClick(e)
                        setIsOpen(false)
                      }
                    }}
                    style={{
                      zIndex: 999999,
                    }}
                  >
                    {item.icon && (
                      <Icon
                        name={item.icon}
                        width={iconWidth}
                        fill={iconFill}
                      />
                    )}
                    {item.label}
                  </div>
                }
                place='right'
              >
                {item.tooltip ?? ''}
              </Tooltip>
            ))}
          </div>,
          document.body,
        )}
    </div>
  )
}

export default DropdownMenu
