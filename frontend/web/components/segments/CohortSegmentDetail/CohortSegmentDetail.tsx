import React, { FC, ReactNode, useEffect, useState } from 'react'
import classNames from 'classnames'
import moment from 'moment'
import Constants from 'common/constants'
import Format from 'common/utils/format'
import Utils from 'common/utils/utils'
import { Segment } from 'common/types/responses'
import {
  useGetCohortQuery,
  useUpdateCohortMutation,
} from 'common/services/useCohort'
import Button from 'components/base/forms/Button'
import Chip from 'components/base/Chip'
import ErrorMessage from 'components/ErrorMessage'
import InputGroup from 'components/base/forms/InputGroup'
import CohortCsvSync from './CohortCsvSync'
import './CohortSegmentDetail.scss'

const SYNC_POLL_INTERVAL_MS = 3000

type CohortSegmentDetailType = {
  projectId: number | string
  segment: Segment
}

const InfoRow: FC<{ label: string; children: ReactNode }> = ({
  children,
  label,
}) => (
  <div className='d-flex align-items-center fs-small'>
    <div className='cohort-segment-detail__info-label text-secondary'>
      {label}
    </div>
    {children}
  </div>
)

const CohortSegmentDetail: FC<CohortSegmentDetailType> = ({
  projectId,
  segment,
}) => {
  const cohort = segment.cohort
  const [name, setName] = useState(segment.name)
  const [description, setDescription] = useState(segment.description || '')
  // Poll while a synchronisation is in flight; the interval derives from the
  // response.
  const [pollingInterval, setPollingInterval] = useState(0)
  const { data } = useGetCohortQuery(
    {
      cohortId: cohort?.id ?? 0,
      environmentApiKey: cohort?.environment_api_key ?? '',
    },
    { pollingInterval, skip: !cohort },
  )
  const [updateCohort, { error: updateError, isLoading: isUpdating }] =
    useUpdateCohortMutation()

  const counts = data?.membership_counts
  const appliedCount = counts?.applied ?? 0
  const pendingCount =
    (counts?.pending_add ?? 0) + (counts?.pending_remove ?? 0)
  const isSyncing = pendingCount > 0
  const identityCount = appliedCount + (counts?.pending_add ?? 0)
  const progressTotal = appliedCount + pendingCount

  useEffect(() => {
    setPollingInterval(isSyncing ? SYNC_POLL_INTERVAL_MS : 0)
  }, [isSyncing])

  useEffect(() => {
    setName(segment.name)
    setDescription(segment.description || '')
  }, [segment.name, segment.description])

  if (!cohort) {
    return null
  }

  const isDirty =
    name !== segment.name || description !== (segment.description || '')

  const save = async () => {
    try {
      await updateCohort({
        cohortId: cohort.id,
        description,
        environmentApiKey: cohort.environment_api_key,
        name,
        projectId: Number(projectId),
        segmentId: segment.id,
      }).unwrap()
      toast('Segment updated')
    } catch (error) {
      console.error('Cohort update failed:', error)
    }
  }

  return (
    <div className='cohort-segment-detail rounded-lg bg-surface-default'>
      <div className='cohort-segment-detail__header d-flex align-items-center gap-2 px-4 py-3'>
        <h5 className='mb-0'>{segment.name}</h5>
        <Chip size='xs' variant='accent'>
          CSV list
        </Chip>
      </div>
      <div className='p-4 d-flex flex-column mx-0 gap-4'>
        <div className='d-flex flex-column mx-0 gap-3'>
          <InputGroup
            className='mb-0'
            title='Name*'
            value={name}
            inputProps={{
              className: 'full-width',
              maxLength: Constants.forms.maxLength.SEGMENT_ID,
            }}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
              setName(
                Format.enumeration
                  .set(Utils.safeParseEventValue(e))
                  .toLowerCase(),
              )
            }}
            isValid={!!name?.length}
            type='text'
            placeholder='E.g. power_users'
          />
          <InputGroup
            className='mb-0'
            title='Description'
            value={description}
            inputProps={{ className: 'full-width' }}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
              setDescription(Utils.safeParseEventValue(e))
            }}
            type='text'
            placeholder="e.g. 'People who have spent over $100' "
          />
          {!!updateError && <ErrorMessage error={updateError} />}
          {isDirty && (
            <div className='text-right'>
              <Button disabled={!name || isUpdating} onClick={save}>
                {isUpdating ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          )}
        </div>
        <div className='cohort-segment-detail__info-panel rounded-lg bg-surface-muted p-3 d-flex flex-column mx-0 gap-2'>
          <InfoRow label='Environment'>
            <span className='fw-semibold'>{cohort.environment_name}</span>
          </InfoRow>
          <InfoRow label='Identities'>
            <span className='fw-semibold'>
              {counts ? identityCount.toLocaleString() : '…'}
            </span>
          </InfoRow>
          {!!data?.last_synced_at && (
            <InfoRow label='Last synchronisation'>
              <span className='fw-semibold'>
                {moment(data.last_synced_at).fromNow()}
              </span>
            </InfoRow>
          )}
          <InfoRow label='Status'>
            <span
              className={classNames(
                'cohort-segment-detail__status d-inline-flex align-items-center gap-1 fw-bold',
                isSyncing
                  ? 'bg-surface-action-tint text-action'
                  : 'bg-surface-success text-success',
              )}
            >
              <span className='cohort-segment-detail__status-dot rounded-circle' />
              {isSyncing ? 'Synchronising' : 'Import completed'}
            </span>
          </InfoRow>
          {isSyncing && (
            <div className='d-flex flex-column mx-0 gap-1'>
              <div className='fs-small text-secondary'>
                {appliedCount.toLocaleString()} of{' '}
                {progressTotal.toLocaleString()} applied
              </div>
              <div className='cohort-segment-detail__progress-track'>
                <div
                  className='cohort-segment-detail__progress-bar bg-surface-action'
                  style={{
                    width: `${
                      progressTotal
                        ? Math.round((appliedCount / progressTotal) * 100)
                        : 0
                    }%`,
                  }}
                />
              </div>
            </div>
          )}
        </div>
        <CohortCsvSync
          cohortId={cohort.id}
          environmentApiKey={cohort.environment_api_key}
          projectId={projectId}
          isSyncing={isSyncing}
        />
      </div>
    </div>
  )
}

export default CohortSegmentDetail
