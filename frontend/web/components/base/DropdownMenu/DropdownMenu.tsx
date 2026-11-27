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

const rowsOf = (menu: HTMLElement) =>
  Array.from(menu.querySelectorAll<HTMLElement>('.ds-dropdown-menu__item'))

// One row is the menu's Tab stop: the chosen option, else the first
const setTabStop = (menu: HTMLElement | null) => {
  if (!menu) return
  const rows = rowsOf(menu)
  const stop = Math.max(
    rows.findIndex((row) => row.getAttribute('aria-checked') === 'true'),
    0,
  )
  rows.forEach((row, i) => (row.tabIndex = i === stop ? 0 : -1))
}

// Arrow keys, Home and End move focus between the rows, and the Tab stop
// moves with it
const moveFocus = (e: KeyboardEvent<HTMLDivElement>) => {
  const rows = rowsOf(e.currentTarget)
  const index = rows.findIndex((row) => row === document.activeElement)
  const next = nextMenuIndex(e.key, index, rows.length)
  if (next === null || !rows.length) return
  e.preventDefault()
  rows.forEach((row, i) => (row.tabIndex = i === next ? 0 : -1))
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
    role='menu'
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
          ref={setTabStop}
          // On desktop the popover panel is the menu; the sheet holds one
          role={asSheet ? 'menu' : undefined}
          aria-label={asSheet ? ariaLabel : undefined}
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
