import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import ModalHR from './ModalHR'

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
      <div className='modal-body'>
        <p>
          This will turn <strong>{feature}</strong> to{' '}
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
      </div>
      <ModalHR />
      <div className='modal-footer'>
        <Button onClick={closeModal} className='mr-2' theme='secondary'>
          Cancel
        </Button>
        <FormGroup className='text-right mb-0'>
          <Button
            onClick={() => {
              onToggleChange(!featureValue)
            }}
            className='btn btn-primary'
            id='confirm-toggle-feature-btn'
          >
            Confirm
          </Button>
        </FormGroup>
      </div>
    </div>
  )
}

export default ConfirmToggleEnvFeature

module.exports = ConfirmToggleEnvFeature
