import React, { FC } from 'react'
import Format from 'common/utils/format'
import { Environment, FeatureState, ProjectFlag } from 'common/types/responses'
import { useGetEnvironmentQuery } from 'common/services/useEnvironment'
import Button from 'components/base/forms/Button'
import ModalHR from './ModalHR'

type ConfirmToggleFeatureType = {
  environmentFlag?: FeatureState
  projectFlag: ProjectFlag
  environmentId: string
  identity?: string
  identityName?: string
  cb: (environments: Environment[]) => void
}

const ConfirmToggleFeature: FC<ConfirmToggleFeatureType> = ({
  cb,
  environmentFlag,
  environmentId,
  identity,
  identityName,
  projectFlag,
}) => {
  const isEnabled = environmentFlag?.enabled
  const { data: environment } = useGetEnvironmentQuery({ id: environmentId })

  return (
    <div id='confirm-toggle-feature-modal'>
      <div className='modal-body'>
        <div>
          This will turn{' '}
          <strong>{Format.enumeration.get(projectFlag.name)}</strong>{' '}
          {isEnabled ? (
            <span className='feature--off'>
              <strong>"Off"</strong>
            </span>
          ) : (
            <span className='feature--on'>
              <strong>"On"</strong>
            </span>
          )}{' '}
          for
          <br />
          <strong>{environment?.name}</strong>
          {identity && (
            <span>
              {' '}
              user <strong>{identityName}.</strong>
              {' Any segment overrides for this feature will now be ignored.'}
            </span>
          )}
        </div>
      </div>
      <ModalHR />
      <div className='modal-footer'>
        <Button theme='secondary' className='mr-2' onClick={closeModal}>
          Cancel
        </Button>
        <Button
          disabled={!environment}
          onClick={() => {
            if (!environment) return
            closeModal()
            cb([environment])
          }}
          className='btn btn-primary'
          id='confirm-toggle-feature-btn'
        >
          Confirm
        </Button>
      </div>
    </div>
  )
}

export default ConfirmToggleFeature
