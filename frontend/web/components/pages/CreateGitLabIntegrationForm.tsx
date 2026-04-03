import React, { FC, useState } from 'react'
import InputGroup from 'components/base/forms/InputGroup'
import Button from 'components/base/forms/Button'
import Utils from 'common/utils/utils'

type CreateGitLabIntegrationFormProps = {
  projectId: string
  onCreate: (args: any) => any
  isCreating: boolean
}

const CreateGitLabIntegrationForm: FC<CreateGitLabIntegrationFormProps> = ({
  isCreating,
  onCreate,
  projectId,
}) => {
  const [instanceUrl, setInstanceUrl] = useState('https://gitlab.com')
  const [accessToken, setAccessToken] = useState('')
  const [webhookSecret, setWebhookSecret] = useState(Utils.GUID())

  const handleSubmit = async () => {
    if (!instanceUrl || !accessToken) return
    const res = await onCreate({
      body: {
        access_token: accessToken,
        gitlab_instance_url: instanceUrl,
        webhook_secret: webhookSecret,
      },
      project_id: parseInt(projectId),
    })
    if ('data' in res) {
      toast('GitLab integration configured')
    } else if ('error' in res) {
      toast('Failed to save integration', 'danger')
    }
  }

  return (
    <div className='px-4 pt-4'>
      <InputGroup
        value={instanceUrl}
        data-test='gitlab-instance-url'
        inputProps={{ name: 'gitlabInstanceUrl' }}
        onChange={(e: InputEvent) => setInstanceUrl(Utils.safeParseEventValue(e))}
        type='text'
        title='GitLab Instance URL'
        tooltip='The base URL of your GitLab instance, e.g. https://gitlab.com'
      />
      <InputGroup
        value={accessToken}
        data-test='gitlab-access-token'
        inputProps={{ name: 'gitlabAccessToken' }}
        onChange={(e: InputEvent) => setAccessToken(Utils.safeParseEventValue(e))}
        type='password'
        title='Access Token'
        tooltip='A group or project access token with api scope (Developer role minimum)'
      />
      <InputGroup
        value={webhookSecret}
        data-test='gitlab-webhook-secret'
        inputProps={{ name: 'gitlabWebhookSecret' }}
        onChange={(e: InputEvent) => setWebhookSecret(Utils.safeParseEventValue(e))}
        type='text'
        title='Webhook Secret (optional)'
        tooltip='Custom secret for webhook validation. Leave as-is to use the auto-generated value.'
      />
      <div className='mt-3'>
        <Button
          theme='primary'
          disabled={!instanceUrl || !accessToken || isCreating}
          onClick={handleSubmit}
        >
          {isCreating ? 'Saving...' : 'Save'}
        </Button>
      </div>
    </div>
  )
}

export default CreateGitLabIntegrationForm
