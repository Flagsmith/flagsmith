import React, { FC, ReactNode, useId } from 'react'
import { Tooltip as ReactTooltip, PlacesType } from 'react-tooltip'
import 'react-tooltip/dist/react-tooltip.css'
import classNames from 'classnames'
import DOMPurify from 'dompurify'

export type TooltipProps = {
  title: ReactNode | React.ReactNode
  children: string | undefined | null
  place?: PlacesType
  plainText?: boolean
  titleClassName?: string
  tooltipClassName?: string
  effect?: 'float' | 'solid'
  afterShow?: () => void
  renderInPortal?: boolean
}

const Tooltip: FC<TooltipProps> = ({
  afterShow,
  children,
  effect,
  place,
  plainText,
  title,
  titleClassName,
  tooltipClassName,
}) => {
  const id = useId().replace(/:/g, '-')

  if (!children) {
    // Skip tooltip by supplying falsy children
    return <>{title}</>
  }

  const content = plainText ? `${children}` : DOMPurify.sanitize(children)

  return (
    <>
      {title && (
        <span
          className={titleClassName}
          data-tooltip-id={id}
          data-tooltip-html={plainText ? undefined : content}
          data-tooltip-content={plainText ? content : undefined}
        >
          {title}
        </span>
      )}
      <ReactTooltip
        className={classNames('rounded', tooltipClassName)}
        id={id}
        place={place || 'top'}
        float={effect === 'float'}
        afterShow={afterShow}
        delayShow={500}
        style={{ wordBreak: 'break-word' }}
      />
    </>
  )
}

export default Tooltip
