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

  const { context, floatingStyles, refs } = useFloating({
    middleware: [
      offset(6),
      flip(),
      shift({ padding: 8 }),
      // Caps the panel at the space left in the window; it scrolls past that.
      size({
        apply({ availableHeight, elements }) {
          elements.floating.style.setProperty(
            '--ds-popover-max-height',
            `${Math.max(availableHeight, 120)}px`,
          )
        },
        padding: 8,
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
    useDismiss(context),
    useRole(context),
  ])

  return (
    <>
      {renderTrigger(
        { ref: refs.setReference, ...getReferenceProps() },
        isOpen,
      )}
      {isOpen && (
        <FloatingPortal>
          <FloatingFocusManager context={context} modal={false}>
            <div
              ref={refs.setFloating}
              // Runtime position from Floating UI.
              style={floatingStyles}
              className={classNames('ds-popover', className)}
              data-placement={context.placement}
              aria-label={ariaLabel}
              {...getFloatingProps()}
            >
              {typeof children === 'function' ? children(close) : children}
            </div>
          </FloatingFocusManager>
        </FloatingPortal>
      )}
    </>
  )
}

export default Popover
