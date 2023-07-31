import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

import * as DOMPurify from 'dompurify'

const ReactTooltip = require('react-tooltip')

type TooltipStylerProps = {
  children: string | JSX.Element | JSX.Element[] | (() => JSX.Element)
}

type TooltipProps = {
  children: string | JSX.Element | JSX.Element[] | (() => JSX.Element)
  htmlEncode: boolean
  place?: string | undefined
  title: string
}

const TooltipStyler = ({ children }: TooltipStylerProps) => (
  <div className='flex-row'>
    <div className='icon--tooltip ion-ios-information-circle mr-1'></div>
    <span>{`${children}`}</span>
  </div>
)

const Tooltip = ({
  children,
  htmlEncode,
  place,
  title,
}: TooltipProps): JSX.Element => {
  const id = Utils.GUID()

  return (
    <span className='question-tooltip'>
      {title ? (
        <span data-for={id} data-tip>
          {title}
        </span>
      ) : (
        <span className='ion ion-ios-help' data-for={id} data-tip />
      )}
      <ReactTooltip
        html
        id={id}
        place={place || 'top'}
        type='dark'
        effect='solid'
      >
        {htmlEncode
          ? renderToStaticMarkup(<TooltipStyler>{children}</TooltipStyler>)
          : DOMPurify.sanitize(
              `<div class="flex-row"><div class="icon--tooltip ion-ios-information-circle mr-1"></div><span>${children}</span></div>`,
            )}
      </ReactTooltip>
    </span>
  )
}

export default Tooltip
