import { AnimationEvent, FC, ReactNode, useId, useRef } from 'react'
import { HeadingText } from 'components/base/typography'
import IconButton from 'components/base/IconButton'
import Icon from 'components/icons/Icon'
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
  // Index of the focusable item to focus on open (defaults to the first)
  initialFocus?: number
}

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

const BottomSheet: FC<BottomSheetProps> = ({
  children,
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
  const sheetRef = useRef<HTMLDivElement | null>(null)
  const titleId = useId()

  const focusInitialItem = () => {
    const items = sheetRef.current?.querySelectorAll<HTMLElement>(FOCUSABLE)
    const target = items?.[initialFocus] ?? sheetRef.current
    target?.focus({ preventScroll: true })
  }

  // Focusing during the slide-in makes the browser scroll to the item, which
  // cuts the animation short (Safari also jumps). Focus once it has finished.
  const onAnimationEnd = (e: AnimationEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) focusInitialItem()
  }

  if (!open) return null

  // No animation runs with reduced motion, so the focus manager focuses on open
  const prefersReducedMotion = !!window.matchMedia?.(
    '(prefers-reduced-motion: reduce)',
  ).matches

  return (
    <FloatingPortal>
      <FloatingOverlay
        className='ds-bottom-sheet__overlay'
        lockScroll
        // The sheet portals out of a row that may be clickable
        onClick={(e) => e.stopPropagation()}
      >
        <FloatingFocusManager
          context={context}
          initialFocus={prefersReducedMotion ? initialFocus : -1}
        >
          <div
            ref={(node) => {
              sheetRef.current = node
              refs.setFloating(node)
            }}
            tabIndex={-1}
            className='ds-bottom-sheet'
            aria-labelledby={titleId}
            onAnimationEnd={onAnimationEnd}
            {...getFloatingProps()}
          >
            <div className='ds-bottom-sheet__header d-flex align-items-center justify-content-between gap-2'>
              <HeadingText id={titleId} level={2} size='sm'>
                {title}
              </HeadingText>
              <IconButton
                aria-label='Close'
                variant='ghost'
                onClick={() => onOpenChange(false)}
              >
                <Icon name='close' width={20} />
              </IconButton>
            </div>
            {children}
          </div>
        </FloatingFocusManager>
      </FloatingOverlay>
    </FloatingPortal>
  )
}

export default BottomSheet
