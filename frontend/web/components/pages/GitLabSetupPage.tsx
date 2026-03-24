import React, { FC, useState } from 'react'
import InputGroup from 'components/base/forms/InputGroup'
import Button from 'components/base/forms/Button'
import Icon from 'components/Icon'
import Utils from 'common/utils/utils'
import {
  useCreateGitlabIntegrationMutation,
  useDeleteGitlabIntegrationMutation,
  useGetGitlabIntegrationQuery,
  useUpdateGitlabIntegrationMutation,
} from 'common/services/useGitlabIntegration'
import { useGetGitlabProjectsQuery } from 'common/services/useGitlab'
import Project from 'common/project'

type GitLabSetupPageType = {
  projectId: string
}

const GitLabSetupPage: FC<GitLabSetupPageType> = ({ projectId }) => {
  const [instanceUrl, setInstanceUrl] = useState<string>('https://gitlab.com')
  const [accessToken, setAccessToken] = useState<string>('')
  const [webhookSecret, setWebhookSecret] = useState<string>(Utils.GUID())
  const [showSecret, setShowSecret] = useState(false)
  const [selectedGitlabProject, setSelectedGitlabProject] = useState<any>(null)

  const [createGitlabIntegration, { isLoading: isCreating }] =
    useCreateGitlabIntegrationMutation()
  const [updateGitlabIntegration] = useUpdateGitlabIntegrationMutation()
  const [deleteGitlabIntegration] = useDeleteGitlabIntegrationMutation()

  const { data: gitlabIntegrations } = useGetGitlabIntegrationQuery(
    { project_id: parseInt(projectId) },
    { skip: !projectId },
  )

  const gitlabIntegration = gitlabIntegrations?.results?.[0]

  const { data: gitlabProjects } = useGetGitlabProjectsQuery(
    { project_id: parseInt(projectId) },
    { skip: !gitlabIntegration },
  )

  const apiHost = Project.api
    ? Project.api.replace(/\/api\/v1\/?$/, '')
    : window.location.origin

  const webhookUrl = `${apiHost}/api/v1/gitlab-webhook/${projectId}/`

  const handleSubmit = async () => {
    if (!instanceUrl || !accessToken) return
    const res = await createGitlabIntegration({
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

  const handleLinkRepo = (gitlabProjectId: number, pathWithNamespace: string) => {
    if (!gitlabIntegration) return
    updateGitlabIntegration({
      body: {
        gitlab_project_id: gitlabProjectId,
        project_name: pathWithNamespace,
      },
      gitlab_integration_id: gitlabIntegration.id,
      project_id: parseInt(projectId),
    }).then((res) => {
      if ('error' in res) {
        toast(`Error: ${JSON.stringify(res.error)}`, 'danger')
      } else {
        toast('GitLab repository linked')
        setSelectedGitlabProject(null)
      }
    })
  }

  const handleDelete = () => {
    if (!gitlabIntegration) return
    openModal2(
      'Delete GitLab Integration',
      <div>
        <p>
          Are you sure you want to delete the GitLab integration? This will
          remove all linked external resources.
        </p>
        <div className='text-right'>
          <Button className='mr-2' onClick={() => closeModal2()}>
            Cancel
          </Button>
          <Button
            theme='danger'
            onClick={() => {
              deleteGitlabIntegration({
                gitlab_integration_id: gitlabIntegration.id,
                project_id: parseInt(projectId),
              }).then(() => {
                toast('GitLab integration deleted')
                closeModal2()
              })
            }}
          >
            Delete
          </Button>
        </div>
      </div>,
    )
  }

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text)
    toast(`${label} copied to clipboard`)
  }

  if (gitlabIntegration) {
    return (
      <div className='px-4 pt-4'>
        <div className='mb-4'>
          <p className='text-muted'>
            Connected to{' '}
            <strong>{gitlabIntegration.gitlab_instance_url}</strong>
          </p>
        </div>

        {/* GitLab repo selection */}
        <div className='mb-4'>
          <label className='fw-bold mb-1'>GitLab Repository</label>
          {gitlabIntegration.project_name ? (
            <div className='d-flex align-items-center'>
              <code className='p-2 rounded flex-fill' style={{ backgroundColor: '#f0f1f3', color: '#1a2634' }}>
                {gitlabIntegration.project_name}
              </code>
              <Button
                theme='text'
                size='small'
                className='ml-2'
                onClick={() => handleLinkRepo(0, '')}
              >
                Change
              </Button>
            </div>
          ) : (
            <div>
              <Select
                size='select-md'
                placeholder='Select a GitLab project to link'
                value={selectedGitlabProject ? {
                  label: selectedGitlabProject.path_with_namespace,
                  value: selectedGitlabProject.id,
                } : null}
                onChange={(v: { value: number }) => {
                  const found = gitlabProjects?.results?.find(
                    (p) => p.id === v.value,
                  )
                  setSelectedGitlabProject(found || null)
                }}
                options={gitlabProjects?.results?.map((p) => ({
                  label: p.path_with_namespace,
                  value: p.id,
                }))}
              />
              {selectedGitlabProject && (
                <Button
                  theme='primary'
                  className='mt-2'
                  onClick={() => handleLinkRepo(
                    selectedGitlabProject.id,
                    selectedGitlabProject.path_with_namespace,
                  )}
                >
                  Save
                </Button>
              )}
            </div>
          )}
        </div>

        {/* Tagging toggle */}
        {gitlabIntegration.project_name && (
          <div className='mb-4'>
            <Row className='align-items-center'>
              <Switch
                checked={gitlabIntegration.tagging_enabled}
                onChange={() => {
                  updateGitlabIntegration({
                    body: {
                      tagging_enabled: !gitlabIntegration.tagging_enabled,
                    },
                    gitlab_integration_id: gitlabIntegration.id,
                    project_id: parseInt(projectId),
                  })
                }}
              />
              <span className='ml-2'>
                Enable automatic tagging of features based on issue/MR state
              </span>
            </Row>
          </div>
        )}

        {/* Webhook config */}
        <div className='mb-4 p-3 rounded' style={{ backgroundColor: '#f8f9fa' }}>
          <label className='fw-bold mb-1'>Webhook Configuration</label>
          <p className='text-muted fs-small'>
            Add this webhook URL to your GitLab project or group settings.
            Enable triggers for: Issues events, Merge request events.
          </p>
          <label className='mb-1'>Webhook URL</label>
          <Row className='align-items-center mb-2'>
            <code className='flex-fill p-2 rounded' style={{ backgroundColor: '#e9ecef', color: '#1a2634' }}>{webhookUrl}</code>
            <Button
              theme='text'
              className='ml-2'
              onClick={() => copyToClipboard(webhookUrl, 'Webhook URL')}
            >
              <Icon name='copy' width={16} />
            </Button>
          </Row>
          <label className='mb-1'>Secret Token</label>
          <Row className='align-items-center'>
            <code className='flex-fill p-2 rounded' style={{ backgroundColor: '#e9ecef', color: '#1a2634' }}>
              {showSecret
                ? gitlabIntegration.webhook_secret
                : '\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022'}
            </code>
            <Button
              theme='text'
              className='ml-2'
              onClick={() => setShowSecret(!showSecret)}
            >
              <Icon name={showSecret ? 'eye-off' : 'eye'} width={16} />
            </Button>
            <Button
              theme='text'
              className='ml-1'
              onClick={() =>
                copyToClipboard(
                  gitlabIntegration.webhook_secret,
                  'Webhook secret',
                )
              }
            >
              <Icon name='copy' width={16} />
            </Button>
          </Row>
        </div>

        <div className='text-right'>
          <Button theme='danger' size='small' onClick={handleDelete}>
            Delete Integration
          </Button>
        </div>
      </div>
    )
  }

  // No integration — show setup form
  return (
    <div className='px-4 pt-4'>
      <InputGroup
        value={instanceUrl}
        data-test='gitlab-instance-url'
        inputProps={{ name: 'gitlabInstanceUrl' }}
        onChange={(e: InputEvent) =>
          setInstanceUrl(Utils.safeParseEventValue(e))
        }
        type='text'
        title='GitLab Instance URL'
        tooltip='The base URL of your GitLab instance, e.g. https://gitlab.com'
      />

      <InputGroup
        value={accessToken}
        data-test='gitlab-access-token'
        inputProps={{ name: 'gitlabAccessToken' }}
        onChange={(e: InputEvent) =>
          setAccessToken(Utils.safeParseEventValue(e))
        }
        type='password'
        title='Access Token'
        tooltip='A group or project access token with api scope (Developer role minimum)'
      />

      <InputGroup
        value={webhookSecret}
        data-test='gitlab-webhook-secret'
        inputProps={{ name: 'gitlabWebhookSecret' }}
        onChange={(e: InputEvent) =>
          setWebhookSecret(Utils.safeParseEventValue(e))
        }
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

export default GitLabSetupPage
