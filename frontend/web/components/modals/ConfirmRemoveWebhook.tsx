import React, { FC, FormEvent, useState } from 'react'
import ProjectProvider from 'common/providers/ProjectProvider'
import { Project } from 'common/types/responses'
import { find } from 'lodash'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils' // we need this to make JSX compile
import Button from 'components/base/forms/Button'

type ConfirmRemoveWebhookType = {
  url: string
  cb: () => void
  projectId: string
  environmentId: string
}

const ConfirmRemoveWebhook: FC<ConfirmRemoveWebhookType> = ({
  cb,
  environmentId,
  projectId,
  url,
}) => {
  const [challenge, setChallenge] = useState()

  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (challenge == url) {
      closeModal()
      cb()
    }
  }

  return (
    <ProjectProvider id={projectId}>
      {({ project }: { project: Project }) => (
        <form id='confirm-remove-feature-modal' onSubmit={submit}>
          <p>
            This will remove <strong>{url}</strong> for the environment{' '}
            <strong>
              {
                find(project.environments, {
                  api_key: environmentId,
                })?.name
              }
            </strong>
            . You should ensure that you do not contain any references to this
            webhook in your applications before proceeding.
          </p>
          <InputGroup
            inputProps={{
              className: 'full-width',
              name: 'confirm-feature-name',
            }}
            title='Please type the webhook url to confirm'
            placeholder='webhook url'
            onChange={(e: InputEvent) => {
              setChallenge(Utils.safeParseEventValue(e))
            }}
          />
          <FormGroup className='text-right'>
            <Button
              type='submit'
              id='confirm-remove-feature-btn'
              disabled={challenge != url}
              className='mt-3'
            >
              Confirm changes
            </Button>
          </FormGroup>
        </form>
      )}
    </ProjectProvider>
  )
}

export default ConfirmRemoveWebhook
