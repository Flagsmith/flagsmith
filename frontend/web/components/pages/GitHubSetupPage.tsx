import React, { FC, useState, useEffect } from 'react'
import _data from 'common/data/base/_data'
import OrganisationSelect from 'components/OrganisationSelect'
import Input from 'components/base/forms/Input'
import InputGroup from 'components/base/forms/InputGroup'
import ProjectFilter from 'components/ProjectFilter'
import Utils from 'common/utils/utils'
import Button from 'components/base/forms/Button'
import { useCreateGithubIntegrationMutation } from 'common/services/useGithubIntegration'
import { useCreateGithubRepositoryMutation } from 'common/services/useGithubRepository'

type GitHubSetupPageType = {}
const GitHubSetupPage: FC<GitHubSetupPageType> = (props) => {
  const installationId =
    new URLSearchParams(props.location.search).get('installation_id') || ''
  console.log('DEBUG: installationId:', installationId)
  const [organisation, setOrganisation] = useState<string>('')
  const [project, setProject] = useState<string>('')
  const [repositoryName, setRepositoryName] = useState<string>('')
  const [repositoryOwner, setRepositoryOwner] = useState<string>('')
  const [repositories, setRepositories] = useState<any>([])
  const [
    createGithubIntegration,
    { data, isSuccess: isSuccessCreateGithubIntegration },
  ] = useCreateGithubIntegrationMutation()

  const [createGithubRepository] = useCreateGithubRepositoryMutation()

  const getRepositories = (installationId: string) => {
    _data
      .get(`http://localhost:3000/api/repositories`, {
        'installation_id': installationId,
      })
      .catch((error) => {
        console.log("DEBUG: error:", error)
      })
      .then((res) => {
        setRepositories(res)
        setRepositoryOwner(res?.repositories[0].owner.login)
      })
  }

  useEffect(() => {
    getRepositories(installationId)
  }, [])

  useEffect(() => {
    if (isSuccessCreateGithubIntegration) {
      toast('Saved')
    }
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

  console.log('DEBUG: organisation:', organisation)

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
          firstOrganisation
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
          onChange={(e: InputEvent) =>
            setRepositoryOwner(Utils.safeParseEventValue(e))
          }
          disabled
          type='text'
          title={'Repository Owner'}
          inputClassName='input--wide'
          placeholder='repositoryOwner'
        />
        <div style={{ width: '300px' }}>
          <Select
            size='select-md'
            placeholder={'Select your repository'}
            onChange={(v) => setRepositoryName(v.label)}
            options={repositories?.repositories?.map((r) => {
              return { label: r.name, value: r.name }
            })}
          />
        </div>
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
