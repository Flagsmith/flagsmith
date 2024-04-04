import React, { FC } from 'react'
import Format from 'common/utils/format'
import ProjectProvider from 'common/providers/ProjectProvider'
import {
  Environment,
  FeatureState,
  Project,
  ProjectFlag,
} from 'common/types/responses'
import { find } from 'lodash'
import Button from 'components/base/forms/Button'
import ModalHR from './ModalHR'

type ConfirmToggleFeatureType = {
  environmentFlag: FeatureState
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

  return (
    <ProjectProvider>
      {({ project }: { project: Project }) => (
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
              <strong>
                {
                  find(project.environments, {
                    api_key: environmentId,
                  })?.name
                }
              </strong>
              {identity && (
                <span>
                  {' '}
                  user <strong>{identityName}.</strong>
                  {
                    ' Any segment overrides for this feature will now be ignored.'
                  }
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
              onClick={() => {
                closeModal()
                cb([
                  find(project.environments, {
                    api_key: environmentId,
                  })!,
                ])
              }}
              className='btn btn-primary'
              id='confirm-toggle-feature-btn'
            >
              Confirm
            </Button>
          </div>
        </div>
      )}
    </ProjectProvider>
  )
}

export default ConfirmToggleFeature
