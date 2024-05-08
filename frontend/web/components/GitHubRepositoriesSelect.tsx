import React, { FC, useEffect, useState } from 'react'
import { Repository } from 'common/types/responses'
import Button from './base/forms/Button'
import { useCreateGithubRepositoryMutation } from 'common/services/useGithubRepository'

export type GitHubRepositoriesSelectType = {
  disabled?: boolean
  repositories: Repository[] | undefined
  organisationId: string
  projectId: string
  githubId: string
}

type repoSelectValue = {
  value: string
}

const GitHubRepositoriesSelect: FC<GitHubRepositoriesSelectType> = ({
  disabled,
  githubId,
  organisationId,
  projectId,
  repositories,
}) => {
  const [
    createGithubRepository,
    { isSuccess: isSuccessCreatedGithubRepository },
  ] = useCreateGithubRepositoryMutation()

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
          createGithubRepository({
            body: {
              project: projectId,
              repository_name: repoData[0],
              repository_owner: repoData[1],
            },
            github_id: githubId,
            organisation_id: organisationId,
          })
        }}
        options={repositories?.map((r: Repository) => {
          return {
            label: `${r.full_name}`,
            value: r.full_name,
          }
        })}
      />
    </div>
  )
}

export default GitHubRepositoriesSelect
