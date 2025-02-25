import React, { FC, useState, useEffect } from 'react'
import OrganisationSelect from 'components/OrganisationSelect'
import Input from 'components/base/forms/Input'
import Icon from 'components/Icon'
import InputGroup from 'components/base/forms/InputGroup'
import ProjectFilter from 'components/ProjectFilter'
import Utils from 'common/utils/utils'
import Button from 'components/base/forms/Button'
import AppActions from 'common/dispatcher/app-actions'
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

type ProjectType = {
  id: string
  name: string
  repo: string
}

type repoType = {
  value: string
  label: string
  name?: string
}

const GitHubSetupPage: FC<GitHubSetupPageType> = ({ location }) => {
  const installationId =
    new URLSearchParams(location.search).get('installation_id') || ''
  const githubIntegrationSetupFromFlagsmithValue: string =
    localStorage?.githubIntegrationSetupFromFlagsmith
  const [organisation, setOrganisation] = useState<string>('')
  const [project, setProject] = useState<any>({})
  const [projects, setProjects] = useState<ProjectType[]>([])
  const [repositoryName, setRepositoryName] = useState<string>('')
  const [repositoryOwner, setRepositoryOwner] = useState<string>('')
  const [repositories, setRepositories] = useState<any>([])

  const { data: repos, isSuccess: reposLoaded } = useGetGithubReposQuery(
    {
      installation_id: installationId,
      organisation_id: organisation,
    },
    { skip: !installationId || !organisation },
  )

  const [createGithubIntegration] = useCreateGithubIntegrationMutation()
  const baseUrl = window.location.origin

  const [
    createGithubRepository,
    { isSuccess: isSuccessCreatedGithubRepository },
  ] = useCreateGithubRepositoryMutation()

  useEffect(() => {
    if (reposLoaded && repos.results) {
      setRepositoryOwner(repos?.results[0].full_name.split('/')[0])
      setRepositories(repos)
    }
  }, [repos, reposLoaded])

  useEffect(() => {
    if (
      isSuccessCreatedGithubRepository &&
      !githubIntegrationSetupFromFlagsmithValue
    ) {
      window.location.href = `${baseUrl}/`
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isSuccessCreatedGithubRepository])

  useEffect(() => {
    if (
      githubIntegrationSetupFromFlagsmithValue &&
      githubIntegrationSetupFromFlagsmithValue === 'install'
    ) {
      createGithubIntegration({
        body: {
          installation_id: installationId,
        },
        organisation_id: JSON.parse(localStorage.lastEnv).orgId,
      }).then(async (res) => {
        if (res?.data && githubIntegrationSetupFromFlagsmithValue) {
          const dataToSend = {
            'installationId': installationId,
          }
          window.opener.postMessage(dataToSend, '*')
        }
      })
    }
  }, [])

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
      {!githubIntegrationSetupFromFlagsmithValue ? (
        <>
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
                setOrganisation(`${organisationId}`)
                AppActions.selectOrganisation(organisationId)
                AppActions.getOrganisation(organisationId)
              }}
              showSettings={false}
              firstOrganisation
            />
          </div>
          <label>
            Select your Flagsmith Project and your Github Repository
          </label>
          <Row className='mb-2'>
            <div style={{ minWidth: '250px' }}>
              <ProjectFilter
                organisationId={parseInt(organisation)}
                onChange={(id: string, name: string) => {
                  setProject({ id, name })
                }}
                value={project.id}
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
                options={repositories?.results?.map((r: repoType) => {
                  return { label: r.name, value: r.name }
                })}
              />
            </div>
            <Button
              theme='primary'
              disabled={
                !(
                  Object.entries(project).length &&
                  installationId &&
                  repositoryName
                )
              }
              onClick={() => {
                const newProjects = [...projects]
                const projectWithRepo = {
                  ...project,
                  repo: repositoryName,
                }
                newProjects.push(projectWithRepo)
                setProjects(newProjects)
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
                <Flex className='table-column px-3'>Repository</Flex>
                <div
                  className='table-column text-center'
                  style={{ width: '80px' }}
                >
                  Remove
                </div>
              </Row>
            }
            renderRow={(v: ProjectType) => (
              <Row className='list-item' key={v.id}>
                <Flex className='table-column px-3'>
                  <div className='font-weight-medium mb-1'>{v.name}</div>
                </Flex>
                <Flex className='table-column px-3'>
                  <div className='font-weight-medium mb-1'>{v.repo}</div>
                </Flex>
                <div
                  className='table-column  text-center'
                  style={{ width: '80px' }}
                >
                  <Button
                    onClick={() => {
                      setProjects(
                        projects.filter((p: ProjectType) => p.repo !== v.repo),
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
              }).then(async (res) => {
                try {
                  if (!githubIntegrationSetupFromFlagsmithValue) {
                    await Promise.all(
                      projects.map(async (project) => {
                        await createGithubRepository({
                          body: {
                            project: project.id,
                            repository_name: project.repo,
                            repository_owner: repositoryOwner,
                          },
                          github_id: res?.data?.id,
                          organisation_id: organisation,
                        })
                      }),
                    )
                    toast('Integration Created')
                  }
                } catch (error) {
                  console.error('Error creating:', error)
                }
              })
            }}
          >
            Save Configuration
          </Button>
        </>
      ) : (
        <h1>Installation Completed</h1>
      )}
    </div>
  )
}

export default GitHubSetupPage
