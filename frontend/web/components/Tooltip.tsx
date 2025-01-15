import React, { FC, ReactNode } from 'react'
import ReactTooltip, { TooltipProps as _TooltipProps } from 'react-tooltip'
import Utils from 'common/utils/utils'
import classNames from 'classnames'
import { sanitize } from 'dompurify'

export type TooltipProps = {
  title: ReactNode
  children: string
  place?: _TooltipProps['place']
  plainText?: boolean
  titleClassName?: string
  tooltipClassName?: string
  effect?: _TooltipProps['effect']
  afterShow?: _TooltipProps['afterShow']
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
  const id = Utils.GUID()

  if (!children) {
    // Skip tooltip by supplying falsy children
    return <>{title}</>
  }
  return (
    <>
      {title && (
        <span className={titleClassName} data-for={id} data-tip>
          {title}
        </span>
      )}
      {!!children && (
        <ReactTooltip
          className={classNames('rounded', tooltipClassName)}
          id={id}
          place={place || 'top'}
          effect={effect}
          afterShow={afterShow}
        >
          {plainText ? (
            `${children}`
          ) : (
            <div
              style={{ wordBreak: 'break-word' }}
              dangerouslySetInnerHTML={{ __html: sanitize(children) }}
            />
          )}
        </ReactTooltip>
      )}
    </>
  )
}

export default Tooltip
