import React, { FC, ReactNode } from 'react'
import Icon, { IconName } from 'components/icons/Icon'
import { buildExperimentArms } from 'components/experiments-v2/steps/AudienceStep'
import {
  ExperimentWizardState,
  MOCK_FLAGS,
} from 'components/experiments-v2/types'
import './LivePreviewPanel.scss'

type LivePreviewPanelProps = {
  wizardState: ExperimentWizardState
}

type NodeStatus = 'configured' | 'pass-through' | 'pending'

type PreviewNodeProps = {
  icon: IconName
  title: string
  summary: ReactNode
  status: NodeStatus
  detail?: ReactNode
}

const PreviewNode: FC<PreviewNodeProps> = ({
  detail,
  icon,
  status,
  summary,
  title,
}) => (
  <div
    className={`live-preview-panel__node live-preview-panel__node--${status}`}
  >
    <div className='live-preview-panel__node-icon'>
      <Icon name={icon} width={16} />
    </div>
    <div className='live-preview-panel__node-body'>
      <span className='live-preview-panel__node-title'>{title}</span>
      <span className='live-preview-panel__node-summary'>{summary}</span>
      {detail && (
        <span className='live-preview-panel__node-detail'>{detail}</span>
      )}
    </div>
  </div>
)

const Connector: FC = () => (
  <div className='live-preview-panel__connector' aria-hidden />
)

const LivePreviewPanel: FC<LivePreviewPanelProps> = ({ wizardState }) => {
  const flag = MOCK_FLAGS.find((f) => f.value === wizardState.featureFlagId)
  const flagLabel = flag?.label ?? 'No flag selected'

  const arms = buildExperimentArms(
    wizardState.controlValue,
    wizardState.variations,
  )
  const armCount = arms.length

  // Identity overrides aren't modelled in MOCK_FLAGS; treat as 0 for the
  // prototype. In production this would come from the flag's identity
  // override count. Cast to number so the JSX comparisons don't narrow.
  const identityOverrideCount = 0 as number
  const segmentOverrides = flag?.existingSegmentOverrides ?? []

  const conditionCount = wizardState.audience.conditions.length
  const samplePercentage = wizardState.audience.samplePercentage

  const weightFor = (armId: string) =>
    wizardState.audience.weights.find((w) => w.armId === armId)?.weight ?? 0

  return (
    <aside className='live-preview-panel'>
      <div className='live-preview-panel__header'>
        <span className='live-preview-panel__header-eyebrow'>Live preview</span>
        <h3 className='live-preview-panel__header-title'>
          {wizardState.details.name || 'Untitled experiment'}
        </h3>
        <span className='live-preview-panel__header-hint'>
          Updates as you fill the form. Reflects the eval hierarchy users go
          through.
        </span>
      </div>

      <div className='live-preview-panel__nodes'>
        <PreviewNode
          icon='flask'
          title='Flag'
          status={flag ? 'configured' : 'pending'}
          summary={flagLabel}
          detail={
            flag ? `${armCount} arm${armCount === 1 ? '' : 's'}` : undefined
          }
        />

        <Connector />

        <PreviewNode
          icon='person'
          title='Identity overrides'
          status={identityOverrideCount > 0 ? 'configured' : 'pass-through'}
          summary={
            identityOverrideCount > 0
              ? `${identityOverrideCount} user${
                  identityOverrideCount === 1 ? '' : 's'
                } excluded`
              : 'No identity overrides'
          }
        />

        <Connector />

        <PreviewNode
          icon='people'
          title='Segment overrides'
          status={segmentOverrides.length > 0 ? 'configured' : 'pass-through'}
          summary={
            segmentOverrides.length > 0
              ? `${segmentOverrides.length} segment override${
                  segmentOverrides.length === 1 ? '' : 's'
                }`
              : 'None'
          }
          detail={
            segmentOverrides.length > 0
              ? `Excluded: ${segmentOverrides
                  .map((s) => s.segmentLabel)
                  .join(', ')}`
              : undefined
          }
        />

        <Connector />

        <PreviewNode
          icon='options-2'
          title='Audience'
          status={conditionCount > 0 ? 'configured' : 'pass-through'}
          summary={
            conditionCount > 0
              ? `${conditionCount} condition${conditionCount === 1 ? '' : 's'}`
              : 'All users in environment'
          }
        />

        <Connector />

        <PreviewNode
          icon='pie-chart'
          title='Allocation'
          status='configured'
          summary={`${samplePercentage}% of eligible users`}
        />

        <Connector />

        <div className='live-preview-panel__variants'>
          <div className='live-preview-panel__variants-label'>Variants</div>
          <div className='live-preview-panel__variants-bar'>
            {arms.map((arm) => {
              const w = weightFor(arm.id)
              if (w === 0) return null
              return (
                <div
                  key={arm.id}
                  className='live-preview-panel__variants-bar-segment'
                  style={{ background: arm.colour, width: `${w}%` }}
                  title={`${arm.name}: ${w}%`}
                />
              )
            })}
          </div>
          <div className='live-preview-panel__variants-list'>
            {arms.map((arm) => (
              <div key={arm.id} className='live-preview-panel__variants-row'>
                <span
                  className='live-preview-panel__variants-dot'
                  style={{ background: arm.colour }}
                />
                <span className='live-preview-panel__variants-name'>
                  {arm.name}
                </span>
                <span className='live-preview-panel__variants-weight'>
                  {weightFor(arm.id)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </aside>
  )
}

LivePreviewPanel.displayName = 'LivePreviewPanel'
export default LivePreviewPanel
