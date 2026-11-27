import { FC, KeyboardEvent, ReactElement, ReactNode } from 'react'
import Popover from 'components/base/Popover'
import IconButton from 'components/base/IconButton'
import Icon from 'components/icons/Icon'
import classNames from 'classnames'
import { DropdownMenuCloseProvider } from './DropdownMenuContext'
import DropdownMenuTrigger from './DropdownMenuTrigger'
import { nextMenuIndex } from './menuFocus'
import './DropdownMenu.scss'

export type DropdownMenuProps = {
  // Names the menu, and the default trigger
  'aria-label': string
  // Any element; it keeps its own handlers and ref. Defaults to a "more"
  // button.
  trigger?: ReactElement
  children: ReactNode
}

// Arrow keys, Home and End move focus between the rows
const moveFocus = (e: KeyboardEvent<HTMLDivElement>) => {
  const rows = Array.from(
    e.currentTarget.querySelectorAll<HTMLElement>('.ds-dropdown-menu__item'),
  )
  const index = rows.findIndex((row) => row === document.activeElement)
  const next = nextMenuIndex(e.key, index, rows.length)
  if (next === null || !rows.length) return
  e.preventDefault()
  rows[next].focus()
}

const DropdownMenu: FC<DropdownMenuProps> = ({
  'aria-label': ariaLabel,
  children,
  trigger,
}) => (
  <Popover
    aria-label={ariaLabel}
    placement='bottom-end'
    renderTrigger={(props) => (
      <DropdownMenuTrigger popoverProps={props}>
        {trigger ?? (
          <IconButton variant='ghost' size='small' aria-label={ariaLabel}>
            <Icon name='more-vertical' width={18} />
          </IconButton>
        )}
      </DropdownMenuTrigger>
    )}
  >
    {(close, asSheet) => (
      <DropdownMenuCloseProvider value={close}>
        <div
          role='menu'
          aria-label={ariaLabel}
          className={classNames('ds-dropdown-menu', {
            // Larger rows in the phone sheet
            'ds-dropdown-menu--sheet': asSheet,
          })}
          onKeyDown={moveFocus}
        >
          {children}
        </div>
      </DropdownMenuCloseProvider>
    )}
  </Popover>
)

export default DropdownMenu
