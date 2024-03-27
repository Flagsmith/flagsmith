import React, { FC, useState, useEffect } from 'react'
import OrganisationSelect from 'components/OrganisationSelect'
import Input from 'components/base/forms/Input'
import Icon from 'components/Icon'
import InputGroup from 'components/base/forms/InputGroup'
import ProjectFilter from 'components/ProjectFilter'
import Utils from 'common/utils/utils'
import Button from 'components/base/forms/Button'
import { useCreateGithubIntegrationMutation } from 'common/services/useGithubIntegration'
import { useCreateGithubRepositoryMutation } from 'common/services/useGithubRepository'
import { useGetGithubReposQuery } from 'common/services/useGithub'
import PanelSearch from 'components/PanelSearch'

type Location = {
  search: string
}

type GitHubSetupPageType = {
  location: Location
}

type projectType = {
  value: string
  label: string
}

type repoType = {
  value: string
  label: string
  name?: string
}

const GitHubSetupPage: FC<GitHubSetupPageType> = ({ location }) => {
  const installationId =
    new URLSearchParams(location.search).get('installation_id') || ''
  const [organisation, setOrganisation] = useState<string>('')
  const [project, setProject] = useState<any>({})
  const [projects, setProjects] = useState<projectType[]>([])
  const [repositoryName, setRepositoryName] = useState<string>('')
  const [repositoryOwner, setRepositoryOwner] = useState<string>('')
  const [repositories, setRepositories] = useState<any>([])

  const { data: repos, isSuccess: reposLoaded } = useGetGithubReposQuery(
    {
      installation_id: installationId,
    },
    { skip: !installationId },
  )

  const [
    createGithubIntegration,
    { data, isSuccess: isSuccessCreateGithubIntegration },
  ] = useCreateGithubIntegrationMutation()
  const baseUrl = window.location.origin

  const [
    createGithubRepository,
    { isSuccess: isSuccessCreatedGithubRepository },
  ] = useCreateGithubRepositoryMutation()

  useEffect(() => {
    if (reposLoaded && repos.repositories) {
      setRepositoryOwner(repos?.repositories[0].owner.login)
      setRepositories(repos)
    }
  }, [repos, reposLoaded])

  useEffect(() => {
    if (isSuccessCreatedGithubRepository) {
      window.location.href = `${baseUrl}/`
    }
  }, [isSuccessCreatedGithubRepository])

  useEffect(() => {
    if (localStorage?.githubIntegrationTrigger) {
      const dataToSend = { 'installationId': installationId }
      window.opener.postMessage(dataToSend, '*')
    }
  }, [])

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
              github_id: data.id,
              organisation_id: organisation,
            })
            promises.push(promise)
          }
          await Promise.all(promises)
          toast('Integration Created')
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
      style={{
        alignContent: 'center',
        display: 'flex',
        flexDirection: 'column',
        flexWrap: 'wrap',
      }}
      className='ml-4 bg-light200'
    >
      <h3 className='my-3'>Configure your integration with GitHub</h3>
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
        <label>Select your Flagsmith Organisation</label>
        <OrganisationSelect
          onChange={(organisationId: string) => {
            setOrganisation(organisationId)
          }}
          showSettings={false}
          firstOrganisation
        />
      </div>
      <label>Select your Flagsmith Project and your Github Repository</label>
      <Row className='mb-2'>
        <div style={{ minWidth: '250px' }}>
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
        <div style={{ width: '250px' }}>
          <Select
            size='select-md'
            placeholder={'Select your repository'}
            onChange={(v: repoType) => setRepositoryName(v.label)}
            options={repositories?.repositories?.map((r: repoType) => {
              return { label: r.name, value: r.name }
            })}
          />
        </div>
        <Button
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
      </Row>
      <PanelSearch
        className='no-pad mb-4'
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
        renderRow={(v: projectType) => (
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
                  setProjects(
                    projects.filter((p: projectType) => p.value !== v.value),
                  )
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
        theme='primary'
        disabled={!projects.length || !installationId || !repositoryName}
        onClick={() => {
          createGithubIntegration({
            body: {
              installation_id: installationId,
            },
            organisation_id: organisation,
          })
        }}
      >
        Save Configuration
      </Button>
    </div>
  )
}

export default GitHubSetupPage