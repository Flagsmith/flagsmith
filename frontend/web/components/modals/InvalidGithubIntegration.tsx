import React, { FC, useState } from 'react'
import Utils from 'common/utils/utils'
import InputGroup from 'components/base/forms/InputGroup'
import Button from 'components/base/forms/Button'
import { useUpdateGithubIntegrationMutation } from 'common/services/useGithubIntegration'
import ErrorMessage from 'components/ErrorMessage'

type InvalidGithubIntegrationType = {
  onComplete?: () => void
  organisationId: string
  githubIntegrationId: string
  errorMessage: string
}

const InvalidGithubIntegration: FC<InvalidGithubIntegrationType> = ({
  errorMessage,
  githubIntegrationId,
  onComplete,
  organisationId,
}) => {
  const [installationId, setInstallationId] = useState<string>('')

  const [updateGithubIntegration, { isLoading: updating }] =
    useUpdateGithubIntegrationMutation()

  return (
    <form
      onSubmit={(e) => {
        Utils.preventDefault(e)
        updateGithubIntegration({
          github_integration_id: githubIntegrationId,
          installation_id: installationId,
          organisation_id: organisationId,
        }).then(() => {
          onComplete?.()
        })
      }}
    >
      <div className='modal-body'>
        <ErrorMessage error={errorMessage} />
        <InputGroup
          title='New Installation ID'
          inputProps={{
            className: 'full-width',
            name: 'installationId',
          }}
          value={installationId}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
            setInstallationId(Utils.safeParseEventValue(event))
          }}
          type='number'
          name='installationId'
          id='installation-id'
          placeholder='E.g. 12345678'
        />
      </div>
      <div className='modal-footer'>
        <Button theme='secondary' className='mr-2' onClick={closeModal}>
          Cancel
        </Button>
        <Button
          id='delete-integration'
          className='mr-2'
          theme='danger'
          data-tests='delete-integration-modal'
        >
          {'Delete the GitHub integration'}
        </Button>
        <Button
          type='submit'
          id='update-installation-id'
          data-tests='update-installation-id'
          disabled={updating || installationId.length === 0}
        >
          {updating ? 'Updating' : 'Update'}
        </Button>
      </div>
    </form>
  )
}

export default InvalidGithubIntegration
