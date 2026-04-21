import React, { FC, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import Banner from 'components/Banner/Banner'
import Button from 'components/base/forms/Button'
import EmptyState from 'components/EmptyState'
import Icon from 'components/icons/Icon'
import SearchableSelect from 'components/base/select/SearchableSelect'
import { OptionType } from 'components/base/select/SearchableSelect'
import {
  ArmWeight,
  CONTROL_ARM_ID,
  CONTROL_COLOUR,
  FlagOption,
  MOCK_SEGMENTS,
  SegmentTrafficConfig,
  Variation,
} from 'components/experiments-v2/types'
import './SegmentTrafficStep.scss'

type Arm = {
  id: string
  name: string
  value: string
  colour: string
}

type SegmentTrafficStepProps = {
  segmentTraffic: SegmentTrafficConfig
  flag: FlagOption | null
  controlValue: string
  variations: Variation[]
  environmentName: string
  onChange: (segmentTraffic: SegmentTrafficConfig) => void
}

export const buildExperimentArms = (
  controlValue: string,
  variations: Variation[],
): Arm[] => [
  {
    colour: CONTROL_COLOUR,
    id: CONTROL_ARM_ID,
    name: 'Control',
    value: controlValue,
  },
  ...variations.map((v) => ({
    colour: v.colour,
    id: v.id,
    name: v.name,
    value: v.value,
  })),
]

export const splitEvenly = (armIds: string[]): ArmWeight[] => {
  if (armIds.length === 0) return []
  const base = Math.floor(100 / armIds.length)
  const remainder = 100 - base * armIds.length
  return armIds.map((id, i) => ({
    armId: id,
    weight: base + (i < remainder ? 1 : 0),
  }))
}

const getWeight = (weights: ArmWeight[] | undefined, armId: string): number =>
  (weights ?? []).find((w) => w.armId === armId)?.weight ?? 0

const SegmentTrafficStep: FC<SegmentTrafficStepProps> = ({
  controlValue,
  environmentName,
  flag,
  onChange,
  segmentTraffic,
  variations,
}) => {
  const { projectId } = useParams<{ projectId?: string }>()
  const segmentsUrl = projectId ? `/project/${projectId}/segments` : undefined

  const arms = useMemo(
    () => buildExperimentArms(controlValue, variations),
    [controlValue, variations],
  )

  const selectedSegment = MOCK_SEGMENTS.find(
    (s) => s.value === segmentTraffic.segmentId,
  )

  if (MOCK_SEGMENTS.length === 0) {
    return (
      <div className='segment-traffic-step'>
        <EmptyState
          title='No segments'
          description='Segments are defined on the Segments page. Create one there, then come back to run an experiment on it.'
          icon='people'
          action={
            segmentsUrl && (
              <a
                className='btn btn-primary btn-sm'
                href={segmentsUrl}
                target='_blank'
                rel='noopener noreferrer'
              >
                Go to Segments page
              </a>
            )
          }
        />
      </div>
    )
  }

  const handleSegmentChange = (segmentId: string) => {
    onChange({ ...segmentTraffic, segmentId })
  }

  const handleWeightChange = (armId: string, value: string) => {
    const newWeight = Math.max(0, Math.min(100, Number(value) || 0))
    const others = arms.filter((a) => a.id !== armId)
    if (others.length === 0) {
      onChange({ ...segmentTraffic, weights: [{ armId, weight: 100 }] })
      return
    }
    const targetOthersTotal = 100 - newWeight
    const currentOthers = others.map((a) => ({
      armId: a.id,
      weight: getWeight(segmentTraffic.weights, a.id),
    }))
    const othersSum = currentOthers.reduce((s, o) => s + o.weight, 0)

    let rebalanced: ArmWeight[]
    if (othersSum === 0) {
      const base = Math.floor(targetOthersTotal / others.length)
      const remainder = targetOthersTotal - base * others.length
      rebalanced = currentOthers.map((o, i) => ({
        armId: o.armId,
        weight: base + (i < remainder ? 1 : 0),
      }))
    } else {
      const scaled = currentOthers.map((o) => {
        const exact = (o.weight / othersSum) * targetOthersTotal
        return { armId: o.armId, exact, floor: Math.floor(exact) }
      })
      const floorSum = scaled.reduce((s, o) => s + o.floor, 0)
      const toDistribute = targetOthersTotal - floorSum
      const byFrac = [...scaled]
        .map((s) => ({ ...s, frac: s.exact - s.floor }))
        .sort((a, b) => b.frac - a.frac)
      byFrac.forEach((s, i) => {
        s.floor += i < toDistribute ? 1 : 0
      })
      const byId = new Map(byFrac.map((s) => [s.armId, s.floor]))
      rebalanced = currentOthers.map((o) => ({
        armId: o.armId,
        weight: byId.get(o.armId) ?? 0,
      }))
    }

    const nextWeights = arms.map((a) => {
      if (a.id === armId) return { armId: a.id, weight: newWeight }
      return (
        rebalanced.find((r) => r.armId === a.id) ?? { armId: a.id, weight: 0 }
      )
    })
    onChange({ ...segmentTraffic, weights: nextWeights })
  }

  const handleSplitEvenly = () => {
    onChange({
      ...segmentTraffic,
      weights: splitEvenly(arms.map((a) => a.id)),
    })
  }

  const hasUserCount =
    selectedSegment !== undefined && selectedSegment.estimatedUsers > 0
  const armEstimates = hasUserCount
    ? arms.map((a) => ({
        arm: a,
        users: Math.round(
          (selectedSegment.estimatedUsers *
            getWeight(segmentTraffic.weights, a.id)) /
            100,
        ),
      }))
    : []

  const conflictingOverride = flag?.existingSegmentOverrides.find(
    (o) => o.segmentId === segmentTraffic.segmentId,
  )

  return (
    <div className='segment-traffic-step'>
      <div className='segment-traffic-step__env'>
        <span className='segment-traffic-step__env-label'>Environment</span>
        <span className='segment-traffic-step__env-value'>
          {environmentName}
        </span>
      </div>

      <section className='segment-traffic-step__section'>
        <div className='segment-traffic-step__section-header'>
          <h4 className='segment-traffic-step__section-title'>
            Target Segment
          </h4>
        </div>
        <label className='segment-traffic-step__label'>Segment</label>
        <SearchableSelect
          value={segmentTraffic.segmentId}
          displayedLabel={selectedSegment?.label}
          onChange={(opt: OptionType) => handleSegmentChange(opt.value)}
          options={MOCK_SEGMENTS}
          placeholder='Select a segment...'
        />
        <span className='segment-traffic-step__hint text-muted fs-small'>
          Users matching this segment will be eligible for the experiment.
          Everyone else sees the flag&apos;s environment default. Need a
          different audience (e.g. a percentage of all users, a combination of
          traits)?{' '}
          {segmentsUrl && (
            <a
              className='segment-traffic-step__segment-link'
              href={segmentsUrl}
              target='_blank'
              rel='noopener noreferrer'
            >
              Create a new segment on the Segments page
            </a>
          )}
          .
        </span>
        {conflictingOverride && flag && (
          <Banner variant='danger'>
            <span>
              <strong>{conflictingOverride.segmentLabel}</strong> already has an
              override on <strong>{flag.label}</strong>. Pick a different
              segment, or remove the existing override on the Features page
              first.
            </span>
          </Banner>
        )}
      </section>

      <section className='segment-traffic-step__section'>
        <div className='segment-traffic-step__section-header'>
          <h4 className='segment-traffic-step__section-title'>Traffic Split</h4>
          <Button theme='outline' size='xSmall' onClick={handleSplitEvenly}>
            Split evenly
          </Button>
        </div>
        <span className='segment-traffic-step__hint text-muted fs-small'>
          Distribute users matching this segment across arms.
        </span>

        <div className='segment-traffic-step__arms'>
          {arms.map((arm) => (
            <div key={arm.id} className='segment-traffic-step__arm-row'>
              <span
                className='segment-traffic-step__arm-dot'
                style={{ background: arm.colour }}
              />
              <span className='segment-traffic-step__arm-name'>{arm.name}</span>
              <div className='segment-traffic-step__arm-input'>
                <input
                  type='number'
                  min={0}
                  max={100}
                  value={getWeight(segmentTraffic.weights, arm.id)}
                  onChange={(e) => handleWeightChange(arm.id, e.target.value)}
                />
                <span>%</span>
              </div>
            </div>
          ))}
        </div>

        <div className='segment-traffic-step__bar'>
          {arms.map((arm) => {
            const w = getWeight(segmentTraffic.weights, arm.id)
            if (w === 0) return null
            return (
              <div
                key={arm.id}
                className='segment-traffic-step__bar-segment'
                style={{ background: arm.colour, width: `${w}%` }}
                title={`${arm.name}: ${w}%`}
              />
            )
          })}
        </div>
      </section>

      {selectedSegment && (
        <div className='segment-traffic-step__sample-estimate'>
          <Icon name='people' width={20} />
          <span>
            {hasUserCount && (
              <>
                Rough split:{' '}
                {armEstimates.map((e, i) => (
                  <React.Fragment key={e.arm.id}>
                    {i > 0 && ' · '}
                    <strong>{e.arm.name}</strong> ~{e.users.toLocaleString()}
                  </React.Fragment>
                ))}
                .{' '}
              </>
            )}
            Actual sample size and time-to-significance depend on traffic,
            baseline rate, and the lift you&apos;re trying to detect.
          </span>
        </div>
      )}
    </div>
  )
}

SegmentTrafficStep.displayName = 'SegmentTrafficStep'
export default SegmentTrafficStep
