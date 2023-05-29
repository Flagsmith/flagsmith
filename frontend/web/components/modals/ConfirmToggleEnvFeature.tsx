import React from 'react'

type ConfirmToggleEnvFeatureType = {
  description: string
  feature: string
  featureValue: boolean
  onToggleChange?: (value: boolean) => void
}

const ConfirmToggleEnvFeature: FC<ConfirmToggleEnvFeatureType> = ({
  description,
  feature,
  featureValue,
  onToggleChange,
}: ConfirmToggleEnvFeatureType) => {
  const isEnabled = featureValue
  return (
    <div id='confirm-toggle-feature-modal'>
      <p>
        This will turn <strong>{feature}</strong> to{' '}
        {isEnabled ? (
          <span className='feature--off'>
            <strong>"Off"</strong>
          </span>
        ) : (
          <span className='feature--on'>
            <strong>"On"</strong>
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
