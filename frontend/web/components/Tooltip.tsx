import React, { FC, ReactElement, ReactNode, useRef } from 'react'
import ReactTooltip, { TooltipProps as _TooltipProps } from 'react-tooltip'
import Utils from 'common/utils/utils'

export type TooltipProps = {
  title: ReactNode
  children: string
  place?: _TooltipProps['place']
  plainText?: boolean
}

const Tooltip: FC<TooltipProps> = ({ children, place, plainText, title }) => {
  const id = Utils.GUID()

  if (!children) {
    // Skip tooltip by supplying falsy children
    return <>{title}</>
  }
  return (
    <>
      {title && (
        <span data-for={id} data-tip>
          {title}
        </span>
      )}
      {!!children && (
        <ReactTooltip className='rounded' id={id} place={place || 'top'}>
          {plainText ? (
            `${children}`
          ) : (
            <div dangerouslySetInnerHTML={{ __html: children }} />
          )}
        </ReactTooltip>
      )}
    </>
  )
}

export default Tooltip
