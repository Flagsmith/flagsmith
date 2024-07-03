import React, { FC, ReactElement, ReactNode, useRef } from 'react'
import ReactTooltip, { TooltipProps as _TooltipProps } from 'react-tooltip'
import Utils from 'common/utils/utils'
import classNames from 'classnames'

export type TooltipProps = {
  title: ReactNode
  children: string
  place?: _TooltipProps['place']
  plainText?: boolean
  titleClassName?: string
  tooltipClassName?: string
}

const Tooltip: FC<TooltipProps> = ({
  children,
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
        >
          {plainText ? (
            `${children}`
          ) : (
            <div
              style={{ wordBreak: 'break-word' }}
              dangerouslySetInnerHTML={{ __html: children }}
            />
          )}
        </ReactTooltip>
      )}
    </>
  )
}

export default Tooltip
