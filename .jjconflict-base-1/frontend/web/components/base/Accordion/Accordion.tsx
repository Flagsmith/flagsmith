import { FC, ReactNode, useId, useState } from 'react'
import cn from 'classnames'
import { colorIconSecondary } from 'common/theme/tokens'
import useCollapsibleHeight from 'common/hooks/useCollapsibleHeight'
import BareButton from 'components/base/forms/BareButton'
import Icon from 'components/icons/Icon'
import './Accordion.scss'

// card: a section of its own. row: an item in a list, which owns the borders.
export type AccordionVariant = 'card' | 'row'

export type AccordionProps = {
  // Laid out as a row, so a chip or spinner can follow the text. It sits
  // inside the toggle, so no links or buttons.
  title: ReactNode
  children: ReactNode
  defaultOpen?: boolean
  // Pass open to control it, e.g. to keep one item of a list open at a time.
  open?: boolean
  onOpenChange?: (open: boolean) => void
  variant?: AccordionVariant
  // For content with its own padding and type, like a table.
  flush?: boolean
  // Blocks toggling, e.g. while the content loads; keeps the open state.
  disabled?: boolean
  className?: string
}

const Accordion: FC<AccordionProps> = ({
  children,
  className,
  defaultOpen = false,
  disabled = false,
  flush = false,
  onOpenChange,
  open,
  title,
  variant = 'card',
}) => {
  const [ownOpen, setOwnOpen] = useState(defaultOpen)
  const isOpen = open ?? ownOpen
  const { contentRef, style } = useCollapsibleHeight(isOpen)
  const id = useId()
  const isCard = variant === 'card'

  const toggle = () => {
    if (open === undefined) setOwnOpen(!isOpen)
    onOpenChange?.(!isOpen)
  }

  return (
    <div
      className={cn(
        'ds-accordion',
        `ds-accordion--${variant}`,
        {
          'bg-surface-default rounded-lg overflow-hidden': isCard,
          'bg-surface-subtle': !isCard && isOpen,
          'ds-accordion--open': isOpen,
        },
        className,
      )}
    >
      <BareButton
        className={cn(
          'ds-accordion__header d-flex w-100 px-3 text-start text-default',
          isCard ? 'gap-2 pt-3' : 'align-items-center gap-3',
          // As in the spec: open content sits right under the title.
          isCard &&
            (isOpen && !flush
              ? 'align-items-start pb-0'
              : 'align-items-center pb-3'),
        )}
        aria-expanded={isOpen}
        aria-controls={`${id}-body`}
        disabled={disabled}
        onClick={toggle}
      >
        <span
          className={cn(
            'ds-accordion__label d-flex align-items-center flex-grow-1',
            isCard ? 'gap-2' : 'gap-3',
          )}
        >
          {title}
        </span>
        <Icon
          name='chevron-down'
          width={isCard ? 24 : 16}
          fill={colorIconSecondary}
          className='ds-accordion__chevron flex-shrink-0'
          aria-hidden
        />
      </BareButton>
      {/* Inert while closed, so its content leaves the tab order. */}
      <div ref={contentRef} style={style} id={`${id}-body`} inert={!isOpen}>
        <div className={cn({ 'ds-accordion__content px-3 pb-3': !flush })}>
          {children}
        </div>
      </div>
    </div>
  )
}

export default Accordion
