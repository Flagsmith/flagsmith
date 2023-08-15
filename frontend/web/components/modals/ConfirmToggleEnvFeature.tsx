import React, { FC } from 'react'
import Button from 'components/base/forms/Button'

type ConfirmToggleEnvFeatureType = {
  description: string
  feature: string
  featureValue: boolean
  onToggleChange: (value: boolean) => void
}

const ConfirmToggleEnvFeature: FC<ConfirmToggleEnvFeatureType> = ({
  description,
  feature,
  featureValue,
  onToggleChange,
}: ConfirmToggleEnvFeatureType) => {
  return (
    <div id='confirm-toggle-feature-modal'>
      <p>
        This will turn <strong>{feature}</strong>{' '}
        {featureValue ? (
          <span className='feature--off'>
            <strong>Off</strong>
          </span>
        ) : (
          <span className='feature--on'>
            <strong>On</strong>
          </span>
        )}
        . <span>{description}</span>
      </p>
      <FormGroup className='text-right'>
        <Button
          onClick={() => {
            onToggleChange(!featureValue)
          }}
          className='btn btn-primary'
          id='confirm-toggle-feature-btn'
        >
          Confirm changes
        </Button>
      </FormGroup>
    </div>
  )
}

export default ConfirmToggleEnvFeature

module.exports = ConfirmToggleEnvFeature
