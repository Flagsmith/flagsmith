import { cloneElement, FC, ReactElement, ReactNode } from 'react'
import Popover, { PopoverPlacement } from 'components/base/Popover'
import { DropdownMenuCloseProvider } from './DropdownMenuContext'
import './DropdownMenu.scss'

export type DropdownMenuProps = {
  'aria-label': string
  // Any element; it receives the ref and open/close props
  trigger: ReactElement
  children: ReactNode
  placement?: PopoverPlacement
}

const DropdownMenu: FC<DropdownMenuProps> = ({
  'aria-label': ariaLabel,
  children,
  placement = 'bottom-end',
  trigger,
}) => (
  <Popover
    aria-label={ariaLabel}
    placement={placement}
    renderTrigger={(props) => cloneElement(trigger, props)}
  >
    {(close) => (
      <DropdownMenuCloseProvider value={close}>
        {/* Items close the menu themselves; this covers plain links */}
        <div className='ds-dropdown-menu' onClick={close}>
          {children}
        </div>
      </DropdownMenuCloseProvider>
    )}
  </Popover>
)

export default DropdownMenu
