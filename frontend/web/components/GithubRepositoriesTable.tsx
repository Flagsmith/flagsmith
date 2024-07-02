import React, { FC, useEffect } from 'react'
import {
  useDeleteGithubRepositoryMutation,
  useUpdateGithubRepositoryMutation,
} from 'common/services/useGithubRepository'
import Button from './base/forms/Button'
import Icon from './Icon'
import PanelSearch from './PanelSearch'
import { GithubRepository } from 'common/types/responses'
import Switch from './Switch'
import Tooltip from './Tooltip'

export type GithubRepositoriesTableType = {
  repos: GithubRepository[] | undefined
  githubId: string
  organisationId: string
}

const GithubRepositoriesTable: FC<GithubRepositoriesTableType> = ({
  githubId,
  organisationId,
  repos,
}) => {
  return (
    <div className='mb-3'>
      <PanelSearch
        className='no-pad mb-4 mt-2'
        title='Repositories'
        items={repos}
        header={
          <Row className='table-header'>
            <Flex className='table-column px-3'>Repository</Flex>
            <div className='table-column '>
              {' '}
              <Tooltip
                title={
                  <div>
                    {'Add Tags and Labels'}
                    <Icon name='info-outlined' />
                  </div>
                }
                place='top'
              >
                {
                  'If enabled, features will be tagged with the GitHub resource type, and the Issue/PR will have the label "Flagsmith flag"'
                }
              </Tooltip>
            </div>
            <div className='table-column text-center' style={{ width: '80px' }}>
              Remove
            </div>
          </Row>
        }
        renderRow={(repo: GithubRepository) => (
          <TableRow
            repo={repo}
            githubId={githubId}
            organisationId={organisationId}
          />
        )}
      />
    </div>
  )
}

const TableRow: FC<{
  githubId: string
  organisationId: string
  repo: GithubRepository
}> = ({ githubId, organisationId, repo }) => {
  const [deleteGithubRepository, { isSuccess: isDeleted }] =
    useDeleteGithubRepositoryMutation()

  useEffect(() => {
    if (isDeleted) {
      toast('Repository unlinked to Project')
    }
  }, [isDeleted])

  const [updateGithubRepository] = useUpdateGithubRepositoryMutation()
  const [taggingenEnabled, setTaggingEnabled] = React.useState(
    repo.tagging_enabled || false,
  )
  return (
    <Row className='list-item' key={repo.id}>
      <Flex className='table-column px-3'>
        <div className='font-weight-medium mb-1'>{`${repo.repository_owner} - ${repo.repository_name}`}</div>
      </Flex>
      <div style={{ width: '105px' }}>
        <Switch
          checked={taggingenEnabled}
          onChange={() => {
            updateGithubRepository({
              body: {
                project: repo.project,
                repository_name: repo.repository_name,
                repository_owner: repo.repository_owner,
                tagging_enabled: !repo.tagging_enabled || false,
              },
              github_id: githubId,
              id: `${repo.id}`,
              organisation_id: organisationId,
            }).then(() => {
              setTaggingEnabled(!taggingenEnabled)
            })
          }}
        />
      </div>
      <div className='table-column  text-center' style={{ width: '80px' }}>
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
  )
}

export default GithubRepositoriesTable
