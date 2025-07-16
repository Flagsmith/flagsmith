import React, { useLayoutEffect, useRef, useState } from 'react'
import Icon, { IconName } from 'components/Icon'
import classNames from 'classnames'
import useOutsideClick from 'common/useOutsideClick'
import { createPortal } from 'react-dom'
import { calculateListPosition } from 'common/utils/calculateListPosition'

type MenuItem = {
  icon?: IconName
  label: string
  onClick: (e: React.MouseEvent) => void
  disabled?: boolean
  tooltip?: string
  dataTest?: string
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
                    className={classNames('feature-action__item', {
                      'feature-action__item_disabled': item.disabled,
                    })}
                    data-test={item.dataTest}
                    onClick={(e) => {
                      e.stopPropagation()
                      if (!item.disabled) {
                        item.onClick(e)
                        setIsOpen(false)
                      }
                    }}
                  >
                    {item.icon && (
                      <Icon
                        name={item.icon}
                        width={iconWidth}
                        fill={iconFill}
                      />
                    )}
                    <span>{item.label}</span>
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
