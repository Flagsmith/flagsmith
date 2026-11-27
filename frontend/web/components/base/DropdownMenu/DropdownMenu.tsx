import { cloneElement, FC, ReactElement, ReactNode } from 'react'
import Popover from 'components/base/Popover'
import IconButton from 'components/base/IconButton'
import Icon from 'components/icons/Icon'
import classNames from 'classnames'
import { useBreakpoint } from 'common/hooks/useBreakpoint'
import { DropdownMenuCloseProvider } from './DropdownMenuContext'
import './DropdownMenu.scss'

export type DropdownMenuProps = {
  // Names the menu, and the default trigger
  'aria-label': string
  // Any element; it receives the ref and open/close props. Defaults to a
  // "more" button.
  trigger?: ReactElement
  children: ReactNode
}

const DropdownMenu: FC<DropdownMenuProps> = ({
  'aria-label': ariaLabel,
  children,
  trigger,
}) => {
  // Popover opens as a sheet on the same breakpoint, where rows get larger
  const asSheet = useBreakpoint('isPhone')
  return (
    <Popover
      aria-label={ariaLabel}
      placement='bottom-end'
      renderTrigger={(props) =>
        cloneElement(
          trigger ?? (
            <IconButton variant='ghost' size='small' aria-label={ariaLabel}>
              <Icon name='more-vertical' width={18} />
            </IconButton>
          ),
          props,
        )
      }
    >
      {(close) => (
        <DropdownMenuCloseProvider value={close}>
          <div
            className={classNames('ds-dropdown-menu', {
              'ds-dropdown-menu--sheet': asSheet,
            })}
          >
            {children}
          </div>
        </DropdownMenuCloseProvider>
      )}
    </Popover>
  )
}

export default DropdownMenu
