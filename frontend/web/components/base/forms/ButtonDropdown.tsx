import { FC, useLayoutEffect, useRef, useState } from 'react'
import Button, { ButtonType, sizeClassNames, themeClassNames } from './Button'
import classNames from 'classnames'
import useOutsideClick from 'common/useOutsideClick'
import Icon, { IconName } from 'components/Icon'

export interface ButtonDropdownType extends ButtonType {
  toggleIcon?: IconName
  dropdownItems: {
    label: string
    onClick: () => void
    disabled?: boolean
  }[]
}

export const ButtonDropdown: FC<ButtonDropdownType> = ({
  children,
  dropdownItems,
  onClick,
  size = 'default',
  theme = 'primary',
  toggleIcon = 'chevron-down',
  ...rest
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [isDropup, setIsDropup] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const menuRef = useRef<HTMLDivElement>(null)

  useOutsideClick(dropdownRef, () => setIsOpen(false))

  useLayoutEffect(() => {
    if (!isOpen || !dropdownRef.current || !menuRef.current) return

    const dropdown = dropdownRef.current
    const menu = menuRef.current

    const rect = dropdown.getBoundingClientRect()

    const dropdownHeight = menu.offsetHeight
    const spaceBelow = window.innerHeight - rect.bottom

    if (spaceBelow < dropdownHeight) {
      setIsDropup(true)
    } else {
      setIsDropup(false)
    }
  }, [isOpen])

  return (
    <div ref={dropdownRef} className='button-dropdown position-relative'>
      <Button
        theme={theme}
        size={size}
        onClick={(e) => {
          onClick?.(e)
          setIsOpen(false)
        }}
        className={classNames(
          {
            'button-dropdown-default': !!dropdownItems?.length,
          },
          rest.className,
        )}
        {...rest}
      >
        {children}
      </Button>
      {!!dropdownItems?.length && (
        <Button
          className={classNames(
            'button-dropdown-toggle',
            themeClassNames[theme],
            sizeClassNames[size],
          )}
          onClick={() => setIsOpen(!isOpen)}
          disabled={rest.disabled}
        >
          <Icon className='m-2' name={toggleIcon} fill='white' />
        </Button>
      )}
      {isOpen && (
        <div
          ref={menuRef}
          className={classNames('feature-action__list border', {
            'placed-bottom': !isDropup,
            'placed-top': isDropup,
          })}
          style={{ right: '0', zIndex: 1000 }}
        >
          {dropdownItems.map((item) => (
            <div
              key={item.label}
              className={classNames('feature-action__item', {
                'feature-action__item_disabled': item.disabled,
              })}
              onClick={() => {
                setIsOpen(false)
                item.onClick()
              }}
            >
              {item.label}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default ButtonDropdown
