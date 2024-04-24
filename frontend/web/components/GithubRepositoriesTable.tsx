import React, { FC, useEffect } from 'react'
import {
  useDeleteGithubRepositoryMutation,
  useGetGithubRepositoriesQuery,
} from 'common/services/useGithubRepository'
import Button from './base/forms/Button'
import Icon from './Icon'
import PanelSearch from './PanelSearch'
import { GithubRepository } from 'common/types/responses'

export type GithubRepositoriesTableType = {
  githubId: string
  organisationId: string
}

const GithubRepositoriesTable: FC<GithubRepositoriesTableType> = ({
  githubId,
  organisationId,
}) => {
  const { data } = useGetGithubRepositoriesQuery({
    github_id: githubId,
    organisation_id: organisationId,
  })

  const [deleteGithubRepository, { isSuccess: isDeleted }] =
    useDeleteGithubRepositoryMutation()

  useEffect(() => {
    if (isDeleted) {
      toast('Repository unlinked to Project')
    }
  }, [isDeleted])

  return (
    <div className='mb-3'>
      <PanelSearch
        className='no-pad mb-4'
        title='Repositories'
        items={data?.results}
        header={
          <Row className='table-header'>
            <Flex className='table-column px-3'>Repository</Flex>
            <div className='table-column text-center' style={{ width: '80px' }}>
              Remove
            </div>
          </Row>
        }
        renderRow={(repo: GithubRepository) => (
          <Row className='list-item' key={repo.id}>
            <Flex className='table-column px-3'>
              <div className='font-weight-medium mb-1'>{`${repo.repository_owner} - ${repo.repository_name}`}</div>
            </Flex>
            <div
              className='table-column  text-center'
              style={{ width: '80px' }}
            >
              <Button
                onClick={() => {
                  openConfirm({
                    body: (
                      <div>
                        {
                          'Are you sure you want to unlink this Repository from this Project'
                        }
                      </div>
                    ),
                    destructive: true,
                    onYes: () => {
                      deleteGithubRepository({
                        github_id: githubId,
                        id: `${repo.id}`,
                        organisation_id: organisationId,
                      })
                    },
                    title: 'Unlink Repository',
                    yesText: 'Confirm',
                  })
                }}
                className='btn btn-with-icon'
              >
                <Icon name='trash-2' width={20} fill='#656D7B' />
              </Button>
            </div>
          </Row>
        )}
      />
    </div>
  )
}

export default GithubRepositoriesTable
