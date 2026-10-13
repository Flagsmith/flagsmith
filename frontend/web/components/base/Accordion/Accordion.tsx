import { FC, ReactNode, useId, useState } from 'react'
import cn from 'classnames'
import { colorIconSecondary } from 'common/theme/tokens'
import useCollapsibleHeight from 'common/hooks/useCollapsibleHeight'
import BareButton from 'components/base/forms/BareButton'
import Icon from 'components/icons/Icon'
import './Accordion.scss'

export type AccordionProps = {
  // Laid out as a row, so a chip or spinner can follow the text. It sits
  // inside the toggle, so no links or buttons.
  title: ReactNode
  children: ReactNode
  defaultOpen?: boolean
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
  title,
}) => {
  const [open, setOpen] = useState(defaultOpen)
  const { contentRef, style } = useCollapsibleHeight(open)
  const id = useId()

  return (
    <div
      className={cn(
        'ds-accordion bg-surface-default rounded-lg overflow-hidden',
        { 'ds-accordion--open': open },
        className,
      )}
    >
      <BareButton
        className={cn(
          'ds-accordion__header d-flex gap-2 w-100 px-3 pt-3 text-start text-default',
          // As in the spec: open content sits right under the title.
          open && !flush ? 'align-items-start pb-0' : 'align-items-center pb-3',
        )}
        aria-expanded={open}
        aria-controls={`${id}-body`}
        disabled={disabled}
        onClick={() => setOpen(!open)}
      >
        <span className='ds-accordion__label d-flex align-items-center flex-grow-1 gap-2'>
          {title}
        </span>
        <Icon
          name='chevron-down'
          width={24}
          fill={colorIconSecondary}
          className='ds-accordion__chevron flex-shrink-0'
          aria-hidden
        />
      </BareButton>
      {/* Inert while closed, so its content leaves the tab order. */}
      <div ref={contentRef} style={style} id={`${id}-body`} inert={!open}>
        <div className={cn({ 'ds-accordion__content px-3 pb-3': !flush })}>
          {children}
        </div>
      </div>
    </div>
  )
}

export default Accordion
