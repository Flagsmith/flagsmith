import React, { FC, useState, useEffect } from 'react'
import OrganisationSelect from 'components/OrganisationSelect'
import ProjectFilter from 'components/ProjectFilter'
import Button from 'components/base/forms/Button'
import { useCreateGithubIntegrationMutation } from 'common/services/useGithubIntegration'
import { useCreateGithubRepositoryMutation } from 'common/services/useGithubRepository'

type GitHubSetupPageType = {}
const GitHubSetupPage: FC<GitHubSetupPageType> = (props) => {
  const installationId =
    new URLSearchParams(props.location.search).get('installation_id') || ''
  const [organisation, setOrganisation] = useState<number>(0)
  const [project, setProject] = useState<number>(0)
  const [repositoryName, setrepositoryName] = useState<string>('')
  const [repositoryOwner, setrepositoryOwner] = useState<string>('')

  const [
    createGithubIntegration,
    { data, isSuccess: isSuccessCreateGithubIntegration },
  ] = useCreateGithubIntegrationMutation()

  const [
    createGithubRepository,
    { isSuccess: isSuccessCreateGithubRepository },
  ] = useCreateGithubRepositoryMutation()

  useEffect(() => {
    toast('Saved')
  }, [isSuccessCreateGithubIntegration])

  useEffect(() => {
    if (data && isSuccessCreateGithubIntegration) {
      createGithubRepository({
        body: {
          project: project,
          repository_name: repositoryName,
          repository_owner: repositoryOwner,
        },
        github_pk: data.id,
        organisation_pk: organisation,
      })
    }
  }, [data, isSuccessCreateGithubIntegration])

  return (
    <div
      id='login-page'
      style={{ flexDirection: 'column' }}
      className='ml-4 bg-light200'
    >
      <h3>Configure your integration with GitHub</h3>
      <InputGroup
        value={installationId}
        data-test='InstallationId'
        inputProps={{
          name: 'InstallationId',
        }}
        disabled
        type='text'
        className={{ width: '500px' }}
        title={'GitHub App Installation Id'}
      />
      <div className='mr-4 mb-4'>
        <p>Select your Organisation</p>
        <OrganisationSelect
          onChange={(organisationId) => {
            setOrganisation(organisationId)
          }}
          showSettings={false}
        />
      </div>
      <Row className='mr-4 mb-4'>
        <div style={{ minWidth: '300px' }}>
          <ProjectFilter
            showAll
            organisationId={organisation}
            onChange={setProject}
            value={project}
          />
        </div>
        <Input
          value={repositoryOwner}
          data-test='repositoryOwner'
          inputProps={{
            name: 'repositoryOwner',
          }}
          onChange={(e) => setrepositoryOwner(Utils.safeParseEventValue(e))}
          ds
          type='text'
          title={'Repository Owner'}
          inputClassName='input--wide'
          placeholder='repositoryOwner'
        />
        <Input
          value={repositoryName}
          data-test='repositoryName'
          inputProps={{
            name: 'repositoryName',
          }}
          onChange={(e) => setrepositoryName(Utils.safeParseEventValue(e))}
          ds
          type='text'
          title={'Repository Name'}
          inputClassName='input--wide'
          placeholder='repositoryName'
        />
      </Row>
      <Button
        className='mr-2 text-right'
        theme='primary'
        disabled={!project || !installationId || !repositoryName}
        onClick={() => {
          createGithubIntegration({
            body: {
              installation_id: installationId,
            },
            organisation_pk: organisation,
          })
        }}
      >
        Save
      </Button>
    </div>
  )
}

export default GitHubSetupPage
