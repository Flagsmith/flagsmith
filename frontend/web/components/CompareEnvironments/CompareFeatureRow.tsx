import React, { FC } from 'react'
import { FeatureState, ProjectFlag } from 'common/types/responses'
import Icon from 'components/icons/Icon'
import Switch from 'components/Switch'
import FeatureName from 'components/feature-summary/FeatureName'
import FeatureValue from 'components/feature-summary/FeatureValue'
import SegmentsIcon from 'components/icons/SegmentsIcon'
import ExpandedRow from './ExpandedRow'
import { ENV_COLUMN_WIDTH, SEGMENTS_COLUMN_WIDTH } from './constants'
import { FeatureChange } from './types'

export type EditFeatureHandler = (
  projectFlag: ProjectFlag,
  environmentFlag: FeatureState,
  environmentKey: string,
  environmentName?: string,
) => void

type CompareFeatureRowProps = {
  item: FeatureChange
  index: number
  projectId: string
  isExpanded: boolean
  onToggle: (featureId: number) => void
  onEdit: EditFeatureHandler
  leftEnvironmentKey: string
  rightEnvironmentKey: string
  leftEnvironmentId?: number
  rightEnvironmentId?: number
  leftEnvironmentName?: string
  rightEnvironmentName?: string
}

type EnvironmentStateCellProps = {
  enabled: boolean
  value: FeatureChange['leftValue']
  onEdit: () => void
  environmentName?: string
}

// The switch and value are read-only representations — clicking either opens
// the edit modal rather than toggling in place
const EnvironmentStateCell: FC<EnvironmentStateCellProps> = ({
  enabled,
  environmentName,
  onEdit,
  value,
}) => (
  <div
    className='clickable d-flex align-items-center gap-2 overflow-hidden'
    role='button'
    tabIndex={0}
    aria-label={`Edit feature state${
      environmentName ? ` in ${environmentName}` : ''
    }`}
    onClick={(e: React.MouseEvent) => {
      e.stopPropagation()
      onEdit()
    }}
    onKeyDown={(e: React.KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        e.stopPropagation()
        onEdit()
      }
    }}
  >
    <Switch className='flex-shrink-0 pe-none' checked={enabled} disabled />
    <FeatureValue className='overflow-hidden' value={value} />
  </div>
)

const CompareFeatureRow: FC<CompareFeatureRowProps> = ({
  index,
  isExpanded,
  item,
  leftEnvironmentId,
  leftEnvironmentKey,
  leftEnvironmentName,
  onEdit,
  onToggle,
  projectId,
  rightEnvironmentId,
  rightEnvironmentKey,
  rightEnvironmentName,
}) => {
  const featureId = item.projectFlagLeft.id
  const totalSegments = Math.max(
    item.projectFlagLeft.num_segment_overrides || 0,
    item.projectFlagRight?.num_segment_overrides || 0,
  )
  const toggle = () => onToggle(featureId)

  const editLeft = () =>
    onEdit(
      item.projectFlagLeft,
      item.leftEnvironmentFlag,
      leftEnvironmentKey,
      leftEnvironmentName,
    )

  const editRight = () =>
    onEdit(
      // Fall back to the left project flag so the modal edits the
      // existing feature instead of switching to create mode
      item.projectFlagRight || item.projectFlagLeft,
      item.rightEnvironmentFlag,
      rightEnvironmentKey,
      rightEnvironmentName,
    )

  return (
    <div className='list-item list-item-xs'>
      <div
        className='clickable d-flex align-items-center py-2'
        data-test={`compare-item-${index}`}
        role='button'
        tabIndex={0}
        aria-expanded={isExpanded}
        onClick={toggle}
        onKeyDown={(e: React.KeyboardEvent) => {
          // Ignore keydowns bubbling from the environment state cells,
          // otherwise activating them via keyboard would also toggle the row
          if (e.target !== e.currentTarget) return
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            toggle()
          }
        }}
      >
        <div className='table-column flex-row flex-fill align-items-center'>
          <Icon
            name={isExpanded ? 'chevron-down' : 'chevron-right'}
            width={16}
            className='me-2'
          />
          <FeatureName name={item.projectFlagLeft.name} />
        </div>

        <div
          className='table-column d-flex align-items-center overflow-hidden'
          style={{ width: ENV_COLUMN_WIDTH }}
        >
          <EnvironmentStateCell
            enabled={item.leftEnabled}
            value={item.leftValue}
            onEdit={editLeft}
            environmentName={leftEnvironmentName}
          />
        </div>

        <div
          className='table-column d-flex align-items-center overflow-hidden'
          style={{ width: ENV_COLUMN_WIDTH }}
        >
          <EnvironmentStateCell
            enabled={item.rightEnabled}
            value={item.rightValue}
            onEdit={editRight}
            environmentName={rightEnvironmentName}
          />
        </div>

        <div
          className='table-column d-flex justify-content-end pe-3'
          style={{ width: SEGMENTS_COLUMN_WIDTH }}
        >
          {totalSegments > 0 && (
            <span className='chip chip--xs bg-primary text-white d-inline-flex align-items-center gap-1'>
              <SegmentsIcon className='chip-svg-icon' />
              {totalSegments}
            </span>
          )}
        </div>
      </div>

      {isExpanded && leftEnvironmentId && rightEnvironmentId && (
        <ExpandedRow
          item={item}
          projectId={projectId}
          environmentLeftId={leftEnvironmentId}
          environmentRightId={rightEnvironmentId}
          oldEnvName={leftEnvironmentName}
          newEnvName={rightEnvironmentName}
        />
      )}
    </div>
  )
}

export default CompareFeatureRow
