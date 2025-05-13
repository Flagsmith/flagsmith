import React, { FC, ReactNode } from 'react'
import ReactTooltip, { TooltipProps as _TooltipProps } from 'react-tooltip'
import Utils from 'common/utils/utils'
import classNames from 'classnames'
import { sanitize } from 'dompurify'
import { createPortal } from 'react-dom'

export type TooltipProps = {
  title: ReactNode | React.ReactNode
  children: string | undefined | null
  place?: _TooltipProps['place']
  plainText?: boolean
  titleClassName?: string
  tooltipClassName?: string
  effect?: _TooltipProps['effect']
  afterShow?: _TooltipProps['afterShow']
  renderInPortal?: boolean // Controls backwards compatibility for rendering in portal
}

const TooltipPortal: FC<{ children: ReactNode; renderInPortal?: boolean }> = ({
  children,
  renderInPortal = false,
}) => {
  const domNode = document.createElement('div')
  document.body.appendChild(domNode)

  if (!renderInPortal) return <>{children}</>
  return domNode ? createPortal(children, domNode) : null
}

const Tooltip: FC<TooltipProps> = ({
  afterShow,
  children,
  effect,
  place,
  plainText,
  renderInPortal,
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
        <TooltipPortal renderInPortal={renderInPortal}>
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
        </TooltipPortal>
      )}
    </>
  )
}

export default Tooltip
