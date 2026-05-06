import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import { IntegrationData } from 'common/types/responses'

type IntegrationCalloutProps = {
  integration: IntegrationData
  ctaLabel?: string
  onClick: () => void
}

const IntegrationCallout: FC<IntegrationCalloutProps> = ({
  ctaLabel = 'Set up',
  integration,
  onClick,
}) => (
  <div className='panel panel-integrations p-3 d-flex align-items-center gap-3'>
    <img
      src={integration.image}
      alt={integration.title}
      style={{ height: 32, width: 32 }}
    />
    <div className='flex-1'>
      <div className='fw-bold'>{integration.title}</div>
      <div className='subtitle'>{integration.description}</div>
    </div>
    <Button size='xSmall' onClick={onClick}>
      {ctaLabel}
    </Button>
  </div>
)

export default IntegrationCallout
