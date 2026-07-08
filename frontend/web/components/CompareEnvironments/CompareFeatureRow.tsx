import React, { FC } from 'react'
import { FeatureState, ProjectFlag } from 'common/types/responses'
import Icon from 'components/icons/Icon'
import Switch from 'components/Switch'
import FeatureName from 'components/feature-summary/FeatureName'
import FeatureValue from 'components/feature-summary/FeatureValue'
import SegmentsIcon from 'components/icons/SegmentsIcon'
import Button from 'components/base/forms/Button'
import ExpandedRow from './ExpandedRow'
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
          className='table-column d-flex align-items-center gap-2'
          style={{ width: 280 }}
        >
          <Switch checked={item.leftEnabled} disabled />
          <FeatureValue value={item.leftValue} />
          <div className='flex-fill' />
          <Button
            theme='text'
            size='xSmall'
            onClick={(e: React.MouseEvent) => {
              e.stopPropagation()
              onEdit(
                item.projectFlagLeft,
                item.leftEnvironmentFlag,
                leftEnvironmentKey,
                leftEnvironmentName,
              )
            }}
          >
            Edit
          </Button>
        </div>

        <div
          className='table-column d-flex align-items-center gap-2'
          style={{ width: 280 }}
        >
          <Switch checked={item.rightEnabled} disabled />
          <FeatureValue value={item.rightValue} />
          <div className='flex-fill' />
          <Button
            theme='text'
            size='xSmall'
            onClick={(e: React.MouseEvent) => {
              e.stopPropagation()
              onEdit(
                // Fall back to the left project flag so the modal edits the
                // existing feature instead of switching to create mode
                item.projectFlagRight || item.projectFlagLeft,
                item.rightEnvironmentFlag,
                rightEnvironmentKey,
                rightEnvironmentName,
              )
            }}
          >
            Edit
          </Button>
        </div>

        <div
          className='table-column d-flex justify-content-end pe-3'
          style={{ width: 140 }}
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
