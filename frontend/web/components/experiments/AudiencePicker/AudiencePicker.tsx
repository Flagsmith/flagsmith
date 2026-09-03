import { FC, useCallback, useMemo } from 'react'
import {
  ExperimentAudienceMatch,
  Segment,
  SegmentCohort,
  SegmentMembership,
} from 'common/types/responses'
import ProjectStore from 'common/stores/project-store'
import InlinePillToggle from 'components/base/forms/InlinePillToggle'
import SegmentSelect from 'components/SegmentSelect'
import AudienceSegmentList from 'components/experiments/AudienceSegmentList'
import {
  AudienceSegment,
  MAX_AUDIENCE_SEGMENTS,
} from 'components/experiments/rollout'
import { isSelectableAudienceSegment } from './utils'

type SegmentOption = {
  value: number
  label: string
  cohort?: SegmentCohort | null
  description?: string
  membership_counts?: SegmentMembership[]
}

type AudiencePickerProps = {
  projectId: number
  environmentId: string
  segments: AudienceSegment[]
  match: ExperimentAudienceMatch
  onSegmentsChange: (segments: AudienceSegment[]) => void
  onMatchChange: (match: ExperimentAudienceMatch) => void
}

const AudiencePicker: FC<AudiencePickerProps> = ({
  environmentId,
  match,
  onMatchChange,
  onSegmentsChange,
  projectId,
  segments,
}) => {
  const isAtCap = segments.length >= MAX_AUDIENCE_SEGMENTS

  const environmentDbId = useMemo(
    () =>
      (ProjectStore.getEnvironmentIdFromKey(environmentId) as
        | number
        | undefined) ?? undefined,
    [environmentId],
  )

  const handleSelect = useCallback(
    (option: SegmentOption | null) => {
      if (!option) return
      onSegmentsChange([
        ...segments,
        {
          cohort: option.cohort,
          description: option.description,
          id: option.value,
          membershipCount: option.membership_counts?.find(
            (membership) => membership.environment === environmentDbId,
          )?.count,
          name: option.label,
        },
      ])
    },
    [environmentDbId, onSegmentsChange, segments],
  )

  const handleRemove = useCallback(
    (id: number) => {
      onSegmentsChange(segments.filter((segment) => segment.id !== id))
    },
    [onSegmentsChange, segments],
  )

  return (
    <div className='d-flex flex-column gap-3'>
      {segments.length ? (
        <AudienceSegmentList
          segments={segments.map((segment) => ({
            cohortSourceType: segment.cohort?.source_type,
            description: segment.description,
            id: segment.id,
            membershipCount: segment.membershipCount,
            name: segment.name,
          }))}
          onRemove={handleRemove}
        />
      ) : (
        <p className='text-muted mb-0'>
          All identities in this environment are eligible. Add a segment to
          narrow the audience.
        </p>
      )}

      {segments.length > 1 && (
        <div className='d-flex align-items-center gap-2'>
          <span className='text-muted'>Enter the experiment when matching</span>
          <InlinePillToggle
            data-test='experiment-audience-match'
            size='small'
            options={[
              { label: 'ANY', value: 'any' },
              { label: 'ALL', value: 'all' },
            ]}
            value={match}
            onChange={onMatchChange}
          />
          <span className='text-muted'>of these segments</span>
        </div>
      )}

      {!isAtCap && (
        <SegmentSelect
          className='w-100'
          data-test='experiment-audience-segment-select'
          membershipCountEnvironmentId={environmentDbId}
          projectId={String(projectId)}
          placeholder='Add a segment...'
          value={undefined}
          filter={(segment: Segment) =>
            isSelectableAudienceSegment(segment, environmentId, segments)
          }
          onChange={handleSelect}
        />
      )}

      {isAtCap && MAX_AUDIENCE_SEGMENTS > 1 && (
        <span className='fs-caption text-muted'>
          An experiment can target up to {MAX_AUDIENCE_SEGMENTS} segments.
        </span>
      )}
    </div>
  )
}

export default AudiencePicker
