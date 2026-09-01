import React, { FC } from 'react'
import moment from 'moment'
import Constants from 'common/constants'
import { useHasPermission } from 'common/providers/Permission'
import {
  useGetCohortSyncKeysQuery,
  useRevokeCohortSyncKeyMutation,
} from 'common/services/useCohort'
import {
  EnvironmentPermission,
  ProjectPermission,
} from 'common/types/permissions.types'
import { CohortSyncKey } from 'common/types/responses'
import Button from 'components/base/forms/Button'
import ErrorMessage from 'components/ErrorMessage'
import Flex from 'components/base/grid/Flex'
import FormGroup from 'components/base/grid/FormGroup'
import Row from 'components/base/grid/Row'
import Icon from 'components/icons/Icon'
import PanelSearch from 'components/PanelSearch'
import Tooltip from 'components/Tooltip'
import CreateCohortSyncKeyModal from './CreateCohortSyncKeyModal'

type CohortSyncTabProps = {
  environmentApiKey: string
  projectId: number | string
}

const CohortSyncTab: FC<CohortSyncTabProps> = ({
  environmentApiKey,
  projectId,
}) => {
  // Key writes need both permissions; mirrors the API's CohortPermission.
  const { permission: canManageOverrides } = useHasPermission({
    id: environmentApiKey,
    level: 'environment',
    permission: EnvironmentPermission.MANAGE_SEGMENT_OVERRIDES,
  })
  const { permission: canManageSegments } = useHasPermission({
    id: `${projectId}`,
    level: 'project',
    permission: ProjectPermission.MANAGE_SEGMENTS,
  })
  const canManage = !!canManageOverrides && !!canManageSegments

  const {
    data: syncKeys,
    error,
    isLoading,
  } = useGetCohortSyncKeysQuery(
    { environmentApiKey },
    { skip: !environmentApiKey },
  )
  const [revokeCohortSyncKey] = useRevokeCohortSyncKeyMutation()

  const handleCreate = () => {
    openModal(
      'Create Cohort Synchronisation Key',
      <CreateCohortSyncKeyModal environmentApiKey={environmentApiKey} />,
      'p-0',
    )
  }

  const handleRevoke = (syncKey: CohortSyncKey) => {
    openConfirm({
      body: (
        <div>
          Any provider using <strong>{syncKey.name}</strong> will stop
          synchronising cohorts into this environment immediately. This cannot
          be undone.
        </div>
      ),
      destructive: true,
      onYes: () => {
        revokeCohortSyncKey({ environmentApiKey, prefix: syncKey.prefix })
          .unwrap()
          .then(() => toast('Cohort synchronisation key revoked'))
          .catch(() =>
            toast('Failed to revoke cohort synchronisation key', 'danger'),
          )
      },
      title: 'Revoke Cohort Synchronisation Key',
      yesText: 'Revoke',
    })
  }

  const filterByName = (syncKey: CohortSyncKey, search: string) =>
    syncKey.name.toLowerCase().includes(search.toLowerCase())

  const renderRow = (syncKey: CohortSyncKey) => (
    <Row className='list-item' key={syncKey.prefix}>
      <Flex className='table-column px-3'>
        <div className='font-weight-medium mb-1'>{syncKey.name}</div>
        <div className='list-item-subtitle'>
          Created {moment(syncKey.created).format('D MMM YYYY')}
        </div>
      </Flex>
      <div className='table-column'>
        <span className='font-monospace fs-small text-muted bg-surface-muted rounded-sm px-2 py-1'>
          {syncKey.prefix}
        </span>
      </div>
      <div className='table-column'>
        {canManage && (
          <Button
            type='button'
            onClick={() => handleRevoke(syncKey)}
            className='btn btn-with-icon'
            aria-label={`Revoke ${syncKey.name}`}
          >
            <Icon name='trash-2' width={20} fill='#656D7B' />
          </Button>
        )}
      </div>
    </Row>
  )

  return (
    <FormGroup className='my-4'>
      <div className='col-md-8'>
        <h5 className='mb-2'>Cohort Synchronisation Keys</h5>
        <p className='fs-small lh-sm mb-0'>
          Cohort synchronisation keys authenticate cohort synchronisation from
          providers such as Mixpanel and Amplitude into this environment.{' '}
          <Button
            theme='text'
            href='https://docs.flagsmith.com/basic-features/segments'
            target='_blank'
            className='fw-normal'
          >
            Learn about Segments.
          </Button>
        </p>
        <p className='fs-small lh-sm mb-4'>
          Key values are shown only once at creation and cannot be recovered
          afterwards.
        </p>
      </div>
      {!!error && <ErrorMessage error={error} />}
      {isLoading && !syncKeys && !error && <Loader />}
      {!error && (!isLoading || !!syncKeys) && (
        <PanelSearch
          id='cohort-sync-keys-list'
          className='no-pad'
          items={syncKeys}
          filterRow={filterByName}
          renderRow={renderRow}
          renderSearchWithNoResults
          actionButton={
            canManage ? (
              <Button
                onClick={handleCreate}
                className='ml-2'
                data-test='create-cohort-sync-key'
              >
                Create Cohort Key
              </Button>
            ) : (
              <Tooltip
                title={
                  <Button className='ml-2' disabled>
                    Create Cohort Key
                  </Button>
                }
                place='left'
              >
                {Constants.cohortSyncKeyPermissions}
              </Tooltip>
            )
          }
          renderNoResults={
            <Row className='list-item p-3 text-muted'>
              You currently have no cohort synchronisation keys for this
              environment.
            </Row>
          }
          isLoading={isLoading}
        />
      )}
    </FormGroup>
  )
}

CohortSyncTab.displayName = 'CohortSyncTab'

export default CohortSyncTab
