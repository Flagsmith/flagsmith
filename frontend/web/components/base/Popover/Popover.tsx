import { FC, ReactNode, useState } from 'react'
import classNames from 'classnames'
import {
  autoUpdate,
  flip,
  FloatingFocusManager,
  FloatingPortal,
  offset,
  shift,
  size,
  useClick,
  useDismiss,
  useFloating,
  useInteractions,
  useRole,
} from '@floating-ui/react'
import { useBreakpoint } from 'common/hooks/useBreakpoint'
import BottomSheet from './BottomSheet'
import './Popover.scss'

export type PopoverTriggerProps = Record<string, unknown> & {
  ref: (node: Element | null) => void
}

// Only these have a matching animation origin in Popover.scss.
export type PopoverPlacement =
  | 'bottom-start'
  | 'bottom-end'
  | 'top-start'
  | 'top-end'

const TRIGGER_GAP = 6
const WINDOW_PADDING = 8

export type PopoverProps = {
  'aria-label': string
  renderTrigger: (props: PopoverTriggerProps, isOpen: boolean) => ReactNode
  children: ReactNode | ((close: () => void) => ReactNode)
  placement?: PopoverPlacement
  className?: string
}

const Popover: FC<PopoverProps> = ({
  'aria-label': ariaLabel,
  children,
  className,
  placement = 'bottom-start',
  renderTrigger,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const close = () => setIsOpen(false)
  const asSheet = useBreakpoint('isPhone')

  const { context, refs, x, y } = useFloating({
    middleware: [
      offset(TRIGGER_GAP),
      flip(),
      shift({ padding: WINDOW_PADDING }),
      // Caps the panel at the space left in the window; it scrolls past that.
      size({
        apply({ availableHeight, elements }) {
          elements.floating.style.setProperty(
            '--ds-popover-max-height',
            `${Math.max(0, availableHeight)}px`,
          )
        },
        padding: WINDOW_PADDING,
      }),
    ],
    onOpenChange: setIsOpen,
    open: isOpen,
    placement,
    // Position with top/left so the CSS entry animation owns `transform`.
    transform: false,
    whileElementsMounted: autoUpdate,
  })
  const { getFloatingProps, getReferenceProps } = useInteractions([
    useClick(context),
    // The sheet handles its own dismiss and role
    useDismiss(context, { enabled: !asSheet }),
    useRole(context, { enabled: !asSheet }),
  ])

  return (
    <>
      {renderTrigger(
        {
          ref: refs.setReference,
          ...getReferenceProps(),
          // useRole is off for the sheet, so state the popup here
          ...(asSheet && {
            'aria-expanded': isOpen,
            'aria-haspopup': 'dialog',
          }),
        },
        isOpen,
      )}
      {asSheet ? (
        <BottomSheet
          open={isOpen}
          onOpenChange={setIsOpen}
          title={ariaLabel}
          className={className}
        >
          {typeof children === 'function' ? children(close) : children}
        </BottomSheet>
      ) : (
        isOpen && (
          <FloatingPortal>
            <FloatingFocusManager context={context} modal={false}>
              <div
                ref={refs.setFloating}
                // Runtime position from Floating UI.
                style={{
                  '--ds-popover-x': `${x}px`,
                  '--ds-popover-y': `${y}px`,
                }}
                className={classNames('ds-popover', className)}
                data-placement={context.placement}
                aria-label={ariaLabel}
                {...getFloatingProps()}
              >
                {typeof children === 'function' ? children(close) : children}
              </div>
            </FloatingFocusManager>
          </FloatingPortal>
        )
      )}
    </>
  )
}

export default Popover
