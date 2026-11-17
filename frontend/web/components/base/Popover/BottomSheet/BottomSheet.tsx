import { FC, ReactNode } from 'react'
import classNames from 'classnames'
import {
  FloatingFocusManager,
  FloatingOverlay,
  FloatingPortal,
  useDismiss,
  useFloating,
  useInteractions,
  useRole,
} from '@floating-ui/react'
import './BottomSheet.scss'

type BottomSheetProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  children: ReactNode
  className?: string
  // Index of the focusable item to focus on open (defaults to the first)
  initialFocus?: number
}

const BottomSheet: FC<BottomSheetProps> = ({
  children,
  className,
  initialFocus = 0,
  onOpenChange,
  open,
  title,
}) => {
  const { context, refs } = useFloating({ onOpenChange, open })
  const { getFloatingProps } = useInteractions([
    useDismiss(context, { outsidePressEvent: 'mousedown' }),
    useRole(context, { role: 'dialog' }),
  ])

  if (!open) return null

  return (
    <FloatingPortal>
      <FloatingOverlay className='ds-bottom-sheet__overlay' lockScroll>
        <FloatingFocusManager context={context} initialFocus={initialFocus}>
          <div
            ref={refs.setFloating}
            className={classNames('ds-bottom-sheet', className)}
            aria-label={title}
            {...getFloatingProps()}
          >
            <div className='ds-bottom-sheet__handle' aria-hidden />
            <div className='ds-bottom-sheet__title'>{title}</div>
            <div className='ds-bottom-sheet__body'>{children}</div>
          </div>
        </FloatingFocusManager>
      </FloatingOverlay>
    </FloatingPortal>
  )
}

export default BottomSheet
