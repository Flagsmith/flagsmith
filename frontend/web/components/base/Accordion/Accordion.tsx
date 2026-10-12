import { FC, ReactNode, useId, useState } from 'react'
import cn from 'classnames'
import { colorIconSecondary } from 'common/theme/tokens'
import useCollapsibleHeight from 'common/hooks/useCollapsibleHeight'
import BareButton from 'components/base/forms/BareButton'
import Icon from 'components/icons/Icon'
import './Accordion.scss'

export type AccordionHeadingLevel = 2 | 3 | 4 | 5 | 6

export type AccordionProps = {
  // Text, a chip or a spinner. It sits inside the toggle, so no links or buttons.
  title: ReactNode
  children: ReactNode
  // Wraps the header in a heading, for an accordion that is a page section.
  headingLevel?: AccordionHeadingLevel
  defaultOpen?: boolean
  // Pass with onOpenChange to control it from outside.
  open?: boolean
  onOpenChange?: (open: boolean) => void
  // Drops the body's padding, for content with its own, like a table.
  flush?: boolean
  className?: string
}

const Accordion: FC<AccordionProps> = ({
  children,
  className,
  defaultOpen = false,
  flush = false,
  headingLevel,
  onOpenChange,
  open: controlledOpen,
  title,
}) => {
  const [uncontrolledOpen, setUncontrolledOpen] = useState(defaultOpen)
  const open = controlledOpen ?? uncontrolledOpen
  const { contentRef, style } = useCollapsibleHeight(open)
  const id = useId()

  const wrapInHeading = (header: ReactNode) => {
    if (!headingLevel) return header
    const Heading = `h${headingLevel}` as const
    return <Heading className='ds-accordion__heading m-0'>{header}</Heading>
  }

  const toggle = () => {
    if (controlledOpen === undefined) setUncontrolledOpen(!open)
    onOpenChange?.(!open)
  }

  return (
    <div
      className={cn(
        'ds-accordion bg-surface-default rounded-lg overflow-hidden',
        { 'ds-accordion--open': open },
        className,
      )}
    >
      {wrapInHeading(
        <BareButton
          className={cn(
            'ds-accordion__header d-flex gap-2 w-100 px-3 pt-3 text-start text-default',
            // Open, the spec tops the title and puts the content right under it.
            open && !flush
              ? 'align-items-start pb-0'
              : 'align-items-center pb-3',
          )}
          aria-expanded={open}
          aria-controls={`${id}-body`}
          aria-labelledby={`${id}-title`}
          onClick={toggle}
        >
          <span id={`${id}-title`} className='ds-accordion__label flex-grow-1'>
            {title}
          </span>
          <Icon
            name='chevron-down'
            width={24}
            fill={colorIconSecondary}
            className='ds-accordion__chevron flex-shrink-0'
            aria-hidden
          />
        </BareButton>,
      )}
      {/* Inert while closed, so its content leaves the tab order and the
          accessibility tree, not just the screen. */}
      <div ref={contentRef} style={style} id={`${id}-body`} inert={!open}>
        <div className={cn({ 'ds-accordion__content px-3 pb-3': !flush })}>
          {children}
        </div>
      </div>
    </div>
  )
}

export default Accordion
