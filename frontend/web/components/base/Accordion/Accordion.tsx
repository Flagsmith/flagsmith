import { FC, ReactNode, useId, useState } from 'react'
import cn from 'classnames'
import { colorIconSecondary } from 'common/theme/tokens'
import useCollapsibleHeight from 'common/hooks/useCollapsibleHeight'
import BareButton from 'components/base/forms/BareButton'
import Icon from 'components/icons/Icon'
import './Accordion.scss'

export type AccordionProps = {
  title: ReactNode
  description?: ReactNode
  // Read with the title, so keep it to text: a status or a count. It sits
  // inside the toggle, so a control here would be nested in a button.
  meta?: ReactNode
  children: ReactNode
  defaultOpen?: boolean
  // Pass with onToggle to control it from outside.
  open?: boolean
  onToggle?: (open: boolean) => void
  // Drops the body's padding, for content with its own, like a table.
  flush?: boolean
  // Stops toggling, for example while its content loads.
  disabled?: boolean
  className?: string
}

const Accordion: FC<AccordionProps> = ({
  children,
  className,
  defaultOpen = false,
  description,
  disabled = false,
  flush = false,
  meta,
  onToggle,
  open: controlledOpen,
  title,
}) => {
  const [uncontrolledOpen, setUncontrolledOpen] = useState(defaultOpen)
  const open = controlledOpen ?? uncontrolledOpen
  const { contentRef, style } = useCollapsibleHeight(open)
  const id = useId()

  const toggle = () => {
    setUncontrolledOpen(!open)
    onToggle?.(!open)
  }

  return (
    <div
      className={cn(
        'ds-accordion bg-surface-default',
        { 'ds-accordion--open': open },
        className,
      )}
    >
      <BareButton
        className='ds-accordion__header d-flex gap-2 w-100 p-3 text-start text-default'
        aria-expanded={open}
        aria-controls={`${id}-body`}
        disabled={disabled}
        onClick={toggle}
      >
        <span className='ds-accordion__heading d-flex flex-grow-1 gap-1'>
          <span>{title}</span>
          {!!description && (
            <span className='text-secondary'>{description}</span>
          )}
        </span>
        {!!meta && <span className='flex-shrink-0'>{meta}</span>}
        <Icon
          name='chevron-down'
          width={24}
          fill={colorIconSecondary}
          className='ds-accordion__chevron flex-shrink-0'
          aria-hidden
        />
      </BareButton>
      {/* Inert while closed, so its content leaves the tab order and the
          accessibility tree, not just the screen. */}
      <div ref={contentRef} style={style} id={`${id}-body`} inert={!open}>
        <div className={cn({ 'px-3 pb-3': !flush })}>{children}</div>
      </div>
    </div>
  )
}

export default Accordion
