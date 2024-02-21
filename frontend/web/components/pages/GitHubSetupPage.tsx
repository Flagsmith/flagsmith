import React, { FC, useState, useEffect } from 'react'
import _data from 'common/data/base/_data'
import OrganisationSelect from 'components/OrganisationSelect'
import Input from 'components/base/forms/Input'
import Icon from 'components/Icon'
import InputGroup from 'components/base/forms/InputGroup'
import ProjectFilter from 'components/ProjectFilter'
import Utils from 'common/utils/utils'
import Button from 'components/base/forms/Button'
import { useCreateGithubIntegrationMutation } from 'common/services/useGithubIntegration'
import { useCreateGithubRepositoryMutation } from 'common/services/useGithubRepository'
import PanelSearch from 'components/PanelSearch'

type GitHubSetupPageType = {}
const GitHubSetupPage: FC<GitHubSetupPageType> = (props) => {
  const installationId =
    new URLSearchParams(props.location.search).get('installation_id') || ''
  const [organisation, setOrganisation] = useState<string>('')
  const [project, setProject] = useState<any>({})
  const [projects, setProjects] = useState<any>([])
  const [repositoryName, setRepositoryName] = useState<string>('')
  const [repositoryOwner, setRepositoryOwner] = useState<string>('')
  const [repositories, setRepositories] = useState<any>([])
  const [
    createGithubIntegration,
    { data, isSuccess: isSuccessCreateGithubIntegration },
  ] = useCreateGithubIntegrationMutation()
  const baseUrl = window.location.origin

  const [
    createGithubRepository,
    { isSuccess: isSuccessCreatedGithubRepository },
  ] = useCreateGithubRepositoryMutation()

  const getRepositories = (installationId: string) => {
    _data
      .get(`http://localhost:3000/api/repositories`, {
        'installation_id': installationId,
      })
      .catch((error) => {
        console.log('DEBUG: error:', error)
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
    if (isSuccessCreatedGithubRepository) {
      window.location.href = `${baseUrl}/`
    }
  }, [isSuccessCreatedGithubRepository])

  useEffect(() => {
    const createRepositories = async () => {
      try {
        if (data && isSuccessCreateGithubIntegration) {
          const promises = []
          for (const project of projects) {
            const promise = createGithubRepository({
              body: {
                project: project.value,
                repository_name: repositoryName,
                repository_owner: repositoryOwner,
              },
              github_pk: data.id,
              organisation_pk: organisation,
            })
            promises.push(promise)
          }
          await Promise.all(promises)
          toast('Saved')
        }
      } catch (error) {
        console.error('Error creating:', error)
      }
    }

    createRepositories()
  }, [
    data,
    isSuccessCreateGithubIntegration,
    projects,
    repositoryName,
    repositoryOwner,
    organisation,
  ])

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
            value={project.value}
            projectComplete={true}
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
      <PanelSearch
        className='no-pad'
        title='Projects'
        items={projects}
        header={
          <Row className='table-header'>
            <Flex className='table-column px-3'>Project</Flex>
            <div className='table-column text-center' style={{ width: '80px' }}>
              Remove
            </div>
          </Row>
        }
        renderRow={(v) => (
          <Row className='list-item' key={v.value}>
            <Flex className='table-column px-3'>
              <div className='font-weight-medium mb-1'>{v.label}</div>
            </Flex>
            <div
              className='table-column  text-center'
              style={{ width: '80px' }}
            >
              <Button
                onClick={() => {
                  setProjects(projects.filter((p) => p.value !== v.value))
                }}
                className='btn btn-with-icon'
              >
                <Icon name='trash-2' width={20} fill='#656D7B' />
              </Button>
            </div>
          </Row>
        )}
      />
      <Button
        className='mr-2 text-right'
        theme='primary'
        disabled={!project || !installationId || !repositoryName}
        onClick={() => {
          {
            const newProjects = [...projects]
            newProjects.push(project)
            setProjects(newProjects)
          }
        }}
      >
        Add Project
      </Button>
      <Button
        className='mr-2 text-right'
        theme='primary'
        disabled={!projects || !installationId || !repositoryName}
        onClick={() => {
          createGithubIntegration({
            body: {
              installation_id: installationId,
            },
            organisation_pk: organisation,
          })
        }}
      >
        Save Configuration
      </Button>
    </div>
  )
}

export default GitHubSetupPage
