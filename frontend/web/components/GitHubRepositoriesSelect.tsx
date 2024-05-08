import React, { FC, useEffect, useState } from 'react'
import { Repository } from 'common/types/responses'
import Button from './base/forms/Button'
import { useCreateGithubRepositoryMutation } from 'common/services/useGithubRepository'
import GithubRepositoriesTable from './GithubRepositoriesTable'
import DeleteGithubIntegracion from './DeleteGithubIntegracion'

export type GitHubRepositoriesSelectType = {
  disabled?: boolean
  repositories: Repository[] | undefined
  organisationId: string
  projectId: string
  githubId: string
  manageIntegration: () => void
}

type repoSelectValue = {
  value: string
}

const GitHubRepositoriesSelect: FC<GitHubRepositoriesSelectType> = ({
  disabled,
  githubId,
  manageIntegration,
  organisationId,
  projectId,
  repositories,
}) => {
  const [
    createGithubRepository,
    { isSuccess: isSuccessCreatedGithubRepository },
  ] = useCreateGithubRepositoryMutation()

  const [repositoryName, setRepositoryName] = useState('')
  const [repositoryOwner, setRepositoryOwner] = useState('')

  useEffect(() => {
    if (isSuccessCreatedGithubRepository) {
      toast('Repository linked with the Project correctly')
    }
  }, [isSuccessCreatedGithubRepository])

  return (
    <div style={{ width: '100%' }}>
      <Select
        size='select-md'
        placeholder={'Select Your Repository'}
        disabled={disabled}
        onChange={(r: repoSelectValue) => {
          const repoData = r.value.split('/')
          setRepositoryName(repoData[0])
          setRepositoryOwner(repoData[1])
        }}
        options={repositories?.map((r: Repository) => {
          return {
            label: `${r.full_name}`,
            value: r.full_name,
          }
        })}
      />
      <div className='text-right mt-2'>
        <Button
          theme='primary'
          disabled={false}
          onClick={() => {
            createGithubRepository({
              body: {
                project: projectId,
                repository_name: repositoryName,
                repository_owner: repositoryOwner,
              },
              github_id: githubId,
              organisation_id: organisationId,
            })
          }}
        >
          Add Repository
        </Button>
      </div>
      <>
        <GithubRepositoriesTable
          githubId={githubId}
          organisationId={organisationId}
        />
        <div className='text-right mt-2'>
          <Button
            className='mr-3'
            id='open-github-win-installations-btn'
            data-test='open-github-win-installations-btn'
            onClick={manageIntegration}
            size='small'
          >
            Manage available GitHub Repositories
          </Button>
          <DeleteGithubIntegracion
            githubId={githubId}
            organisationId={organisationId}
            onConfirm={() => {
              window.location.reload()
            }}
          />
        </div>
      </>
    </div>
  )
}

export default GitHubRepositoriesSelect
