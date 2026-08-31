import React, { FC } from 'react'
import moment from 'moment'
import Constants from 'common/constants'
import { useHasPermission } from 'common/providers/Permission'
import {
  useGetCohortSyncKeysQuery,
  useRevokeCohortSyncKeyMutation,
} from 'common/services/useCohort'
import { EnvironmentPermission } from 'common/types/permissions.types'
import { CohortSyncKey } from 'common/types/responses'
import Button from 'components/base/forms/Button'
import Flex from 'components/base/grid/Flex'
import FormGroup from 'components/base/grid/FormGroup'
import Panel from 'components/base/grid/Panel'
import Row from 'components/base/grid/Row'
import Icon from 'components/icons/Icon'
import Loader from 'components/Loader'
import PanelSearch from 'components/PanelSearch'
import Tooltip from 'components/Tooltip'
import CreateCohortSyncKeyModal from './CreateCohortSyncKeyModal'

type CohortSyncTabProps = {
  environmentApiKey: string
}

const CohortSyncTab: FC<CohortSyncTabProps> = ({ environmentApiKey }) => {
  const { permission: canManage } = useHasPermission({
    id: environmentApiKey,
    level: 'environment',
    permission: EnvironmentPermission.MANAGE_SEGMENT_OVERRIDES,
  })

  const { data: syncKeys, isLoading } = useGetCohortSyncKeysQuery(
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
        <Button
          type='button'
          onClick={() => handleRevoke(syncKey)}
          className='btn btn-with-icon'
          aria-label={`Revoke ${syncKey.name}`}
        >
          <Icon name='trash-2' width={20} fill='#656D7B' />
        </Button>
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
        <p className='fs-small lh-sm mb-0'>
          Key values are shown only once at creation and cannot be recovered
          afterwards.
        </p>
        {canManage ? (
          <Button
            onClick={handleCreate}
            className='my-4'
            data-test='create-cohort-sync-key'
          >
            Create Cohort Synchronisation Key
          </Button>
        ) : (
          <Tooltip
            title={
              <Button className='my-4' disabled>
                Create Cohort Synchronisation Key
              </Button>
            }
            place='right'
          >
            {Constants.environmentPermissions(
              EnvironmentPermission.MANAGE_SEGMENT_OVERRIDES,
            )}
          </Tooltip>
        )}
      </div>
      {isLoading && !syncKeys ? (
        <Loader />
      ) : (
        <PanelSearch
          id='cohort-sync-keys-list'
          title='Cohort Synchronisation Keys'
          className='no-pad'
          items={syncKeys}
          filterRow={filterByName}
          renderRow={renderRow}
          renderNoResults={
            <Panel className='no-pad' title='Cohort Synchronisation Keys'>
              <div className='search-list'>
                <Row className='list-item p-3 text-muted'>
                  You currently have no cohort synchronisation keys for this
                  environment.
                </Row>
              </div>
            </Panel>
          }
          isLoading={isLoading}
        />
      )}
    </FormGroup>
  )
}

CohortSyncTab.displayName = 'CohortSyncTab'

export default CohortSyncTab
