import { FC, ReactNode, useEffect, useState } from 'react'
import { useHistory } from 'react-router-dom'
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
  // A function gets close, and whether the panel is the phone sheet
  children: ReactNode | ((close: () => void, asSheet: boolean) => ReactNode)
  placement?: PopoverPlacement
  // Applies to the desktop panel only; the phone sheet sizes itself.
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
  // Back or forward leaves the page, so an open popover goes with it. There
  // is no router in stories
  const history = useHistory()
  useEffect(() => history?.listen(() => setIsOpen(false)), [history])

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
          // The trigger and panel can sit in a clickable row, and React
          // bubbles portal events through it, so stop them here
          ...getReferenceProps({
            onClick: (e) => e.stopPropagation(),
            onKeyDown: (e) => e.stopPropagation(),
          }),
          // useRole is off for the sheet, so state the popup here
          ...(asSheet && {
            'aria-expanded': isOpen,
            'aria-haspopup': 'dialog',
          }),
        },
        isOpen,
      )}
      {asSheet ? (
        <BottomSheet open={isOpen} onOpenChange={setIsOpen} title={ariaLabel}>
          {isOpen &&
            (typeof children === 'function'
              ? children(close, asSheet)
              : children)}
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
                // Keys pass through, so Escape still closes it
                {...getFloatingProps({ onClick: (e) => e.stopPropagation() })}
              >
                {typeof children === 'function'
                  ? children(close, asSheet)
                  : children}
              </div>
            </FloatingFocusManager>
          </FloatingPortal>
        )
      )}
    </>
  )
}

export default Popover
