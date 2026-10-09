import { FC, ReactNode, useId, useState } from 'react'
import cn from 'classnames'
import { colorIconSecondary } from 'common/theme/tokens'
import useCollapsibleHeight from 'common/hooks/useCollapsibleHeight'
import BareButton from 'components/base/forms/BareButton'
import Icon from 'components/icons/Icon'
import Loader from 'components/Loader'
import './Accordion.scss'

export type AccordionHeadingLevel = 2 | 3 | 4 | 5 | 6

export type AccordionProps = {
  title: ReactNode
  // Shown under the title once open, as in the spec.
  description?: ReactNode
  // Read with the title, so keep it to text: a status or a count. It sits
  // inside the toggle, so a control here would be nested in a button.
  meta?: ReactNode
  children: ReactNode
  // The header's heading level, so the sections show up in heading navigation.
  headingLevel?: AccordionHeadingLevel
  defaultOpen?: boolean
  // Pass with onToggle to control it from outside.
  open?: boolean
  onToggle?: (open: boolean) => void
  // Drops the body's padding, for content with its own, like a table.
  flush?: boolean
  // Shows a spinner and stops toggling until the content is ready.
  isLoading?: boolean
  className?: string
}

const Accordion: FC<AccordionProps> = ({
  children,
  className,
  defaultOpen = false,
  description,
  flush = false,
  headingLevel = 3,
  isLoading = false,
  meta,
  onToggle,
  open: controlledOpen,
  title,
}) => {
  const [uncontrolledOpen, setUncontrolledOpen] = useState(defaultOpen)
  const open = controlledOpen ?? uncontrolledOpen
  const { contentRef, style } = useCollapsibleHeight(open)
  const id = useId()
  const Heading = `h${headingLevel}` as const

  const toggle = () => {
    // aria-disabled rather than disabled, so it stays focusable and is found.
    if (isLoading) return
    setUncontrolledOpen(!open)
    onToggle?.(!open)
  }

  // Named by the title alone; the description and status are read after it.
  const describedBy = [
    open && description && `${id}-description`,
    (meta || isLoading) && `${id}-meta`,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div
      className={cn(
        'ds-accordion bg-surface-default overflow-hidden',
        { 'ds-accordion--open': open },
        className,
      )}
    >
      <Heading className='ds-accordion__level'>
        <BareButton
          className={cn(
            'ds-accordion__header d-flex gap-2 w-100 p-3 text-start text-default',
            open ? 'align-items-start' : 'align-items-center',
          )}
          aria-expanded={open}
          aria-controls={`${id}-body`}
          aria-labelledby={`${id}-title`}
          aria-describedby={describedBy || undefined}
          aria-disabled={isLoading || undefined}
          onClick={toggle}
        >
          <span className='ds-accordion__heading d-flex flex-grow-1 gap-1'>
            <span id={`${id}-title`}>{title}</span>
            {open && !!description && (
              <span id={`${id}-description`}>{description}</span>
            )}
          </span>
          {(!!meta || isLoading) && (
            <span id={`${id}-meta`} className='flex-shrink-0'>
              {isLoading ? <Loader width='15px' height='15px' /> : meta}
            </span>
          )}
          <Icon
            name='chevron-down'
            width={24}
            fill={colorIconSecondary}
            className='ds-accordion__chevron flex-shrink-0'
            aria-hidden
          />
        </BareButton>
      </Heading>
      {/* Inert while closed, so its content leaves the tab order and the
          accessibility tree, not just the screen. */}
      <div
        ref={contentRef}
        style={style}
        id={`${id}-body`}
        inert={!open}
        aria-busy={isLoading || undefined}
      >
        <div className={cn({ 'px-3 pb-3': !flush })}>{children}</div>
      </div>
    </div>
  )
}

export default Accordion
