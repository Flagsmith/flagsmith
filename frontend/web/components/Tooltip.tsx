import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

import * as DOMPurify from 'dompurify'
import Utils from 'common/utils/utils'
import { informationCircle } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'

const ReactTooltip = require('react-tooltip')

type StyledTooltipProps = {
  children: string
}

type TooltipProps = {
  children: string
  plainText: boolean
  place?: string | undefined
  title: JSX.Element // This is actually the Tooltip parent component
}

const StyledTooltip = ({ children }: StyledTooltipProps) => (
  <div className='flex-row'>
    <div className='icon--new-tooltip mr-1'>
      <IonIcon icon={informationCircle} />
    </div>
    <span>{`${children}`}</span>
  </div>
)

const tooltipStyler = (plainText: boolean, children: string): string => {
  const html = renderToStaticMarkup(
    <StyledTooltip>{plainText ? children : '{{html}}'}</StyledTooltip>,
  )
  if (plainText) {
    return html
  }
  return html.replace('{{html}}', DOMPurify.sanitize(children.toString()))
}

const Tooltip = ({
  children,
  place,
  plainText,
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
        {tooltipStyler(plainText, children)}
      </ReactTooltip>
    </span>
  )
}

export default Tooltip
