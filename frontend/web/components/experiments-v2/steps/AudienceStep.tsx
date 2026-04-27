import React, { FC, useMemo } from 'react'
import { useParams } from 'react-router-dom'
import Banner from 'components/Banner/Banner'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import SearchableSelect from 'components/base/select/SearchableSelect'
import { OptionType } from 'components/base/select/SearchableSelect'
import {
  ArmWeight,
  AudienceConfig,
  CONTROL_ARM_ID,
  CONTROL_COLOUR,
  FlagOption,
  MOCK_ENVIRONMENT_USER_COUNT,
  MOCK_SEGMENTS,
  SAMPLE_SIZE_PRESETS,
  Variation,
} from 'components/experiments-v2/types'
import './AudienceStep.scss'

type Arm = {
  id: string
  name: string
  value: string
  colour: string
}

type AudienceStepProps = {
  audience: AudienceConfig
  flag: FlagOption | null
  controlValue: string
  variations: Variation[]
  environmentName: string
  onChange: (audience: AudienceConfig) => void
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

const clampSamplePercentage = (value: number): number =>
  Math.max(1, Math.min(100, Math.round(value)))

const AudienceStep: FC<AudienceStepProps> = ({
  audience,
  controlValue,
  environmentName,
  flag,
  onChange,
  variations,
}) => {
  const { projectId } = useParams<{ projectId?: string }>()
  const segmentsUrl = projectId ? `/project/${projectId}/segments` : undefined

  const arms = useMemo(
    () => buildExperimentArms(controlValue, variations),
    [controlValue, variations],
  )

  const selectedSegment = MOCK_SEGMENTS.find(
    (s) => s.value === audience.segmentId,
  )

  const handleSegmentChange = (segmentId: string | null) => {
    onChange({ ...audience, segmentId })
  }

  const handleSamplePercentageChange = (next: number) => {
    onChange({ ...audience, samplePercentage: clampSamplePercentage(next) })
  }

  const handleWeightChange = (armId: string, value: string) => {
    const newWeight = Math.max(0, Math.min(100, Number(value) || 0))
    const others = arms.filter((a) => a.id !== armId)
    if (others.length === 0) {
      onChange({ ...audience, weights: [{ armId, weight: 100 }] })
      return
    }
    const targetOthersTotal = 100 - newWeight
    const currentOthers = others.map((a) => ({
      armId: a.id,
      weight: getWeight(audience.weights, a.id),
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
    onChange({ ...audience, weights: nextWeights })
  }

  const handleSplitEvenly = () => {
    onChange({
      ...audience,
      weights: splitEvenly(arms.map((a) => a.id)),
    })
  }

  const eligibleUsers =
    selectedSegment?.estimatedUsers ?? MOCK_ENVIRONMENT_USER_COUNT
  const sampledUsers = Math.round(
    (eligibleUsers * audience.samplePercentage) / 100,
  )

  const armEstimates = arms.map((a) => ({
    arm: a,
    users: Math.round((sampledUsers * getWeight(audience.weights, a.id)) / 100),
  }))

  const conflictingOverride = audience.segmentId
    ? flag?.existingSegmentOverrides.find(
        (o) => o.segmentId === audience.segmentId,
      )
    : undefined

  const isCustomSamplePercentage = !SAMPLE_SIZE_PRESETS.includes(
    audience.samplePercentage as (typeof SAMPLE_SIZE_PRESETS)[number],
  )

  return (
    <div className='audience-step'>
      <div className='audience-step__env'>
        <div className='audience-step__env-item'>
          <span className='audience-step__env-label'>Environment</span>
          <span className='audience-step__env-value'>{environmentName}</span>
        </div>
        <span className='audience-step__env-divider' aria-hidden />
        <div className='audience-step__env-item'>
          <span className='audience-step__env-label'>Bucketed by</span>
          <span className='audience-step__env-value'>identity</span>
        </div>
      </div>

      <section className='audience-step__section'>
        <div className='audience-step__section-header'>
          <h4 className='audience-step__section-title'>
            Targeting
            <span className='audience-step__optional-badge'>Optional</span>
          </h4>
          {audience.segmentId && (
            <Button
              theme='text'
              size='xSmall'
              onClick={() => handleSegmentChange(null)}
            >
              Clear filter
            </Button>
          )}
        </div>
        <span className='audience-step__hint text-muted fs-small'>
          Filter the experiment to a specific segment of users. Leave empty to
          run on all identities in the environment.
        </span>
        <SearchableSelect
          value={audience.segmentId ?? ''}
          displayedLabel={selectedSegment?.label ?? 'All users'}
          onChange={(opt: OptionType) => handleSegmentChange(opt.value)}
          options={MOCK_SEGMENTS}
          placeholder='All users in this environment'
        />
        {segmentsUrl && (
          <span className='audience-step__hint text-muted fs-small'>
            Need a different filter (combination of traits, geography, plan)?{' '}
            <a
              className='audience-step__segment-link'
              href={segmentsUrl}
              target='_blank'
              rel='noopener noreferrer'
            >
              Create a new segment on the Segments page
            </a>
            .
          </span>
        )}
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

      <section className='audience-step__section'>
        <div className='audience-step__section-header'>
          <h4 className='audience-step__section-title'>Sample size</h4>
        </div>
        <span className='audience-step__hint text-muted fs-small'>
          What percentage of eligible users enters the experiment? The rest keep
          the flag&apos;s environment default and aren&apos;t part of the
          result.
        </span>
        <div className='audience-step__sample-presets'>
          {SAMPLE_SIZE_PRESETS.map((preset) => {
            const isActive =
              !isCustomSamplePercentage && audience.samplePercentage === preset
            return (
              <button
                key={preset}
                type='button'
                className={`audience-step__sample-preset${
                  isActive ? ' audience-step__sample-preset--active' : ''
                }`}
                onClick={() => handleSamplePercentageChange(preset)}
              >
                {preset}%
              </button>
            )
          })}
          <button
            type='button'
            className={`audience-step__sample-preset${
              isCustomSamplePercentage
                ? ' audience-step__sample-preset--active'
                : ''
            }`}
            onClick={() => handleSamplePercentageChange(75)}
          >
            Custom
          </button>
        </div>
        {isCustomSamplePercentage && (
          <div className='audience-step__sample-custom'>
            <input
              type='number'
              min={1}
              max={100}
              value={audience.samplePercentage}
              onChange={(e) =>
                handleSamplePercentageChange(Number(e.target.value) || 1)
              }
            />
            <span>%</span>
          </div>
        )}
      </section>

      <section className='audience-step__section'>
        <div className='audience-step__section-header'>
          <h4 className='audience-step__section-title'>Variation split</h4>
          <Button theme='outline' size='xSmall' onClick={handleSplitEvenly}>
            Split evenly
          </Button>
        </div>
        <span className='audience-step__hint text-muted fs-small'>
          Distribute sampled users across control and treatment variations.
          Control takes one of the slots; weights must sum to 100.
        </span>

        <div className='audience-step__arms'>
          {arms.map((arm) => (
            <div key={arm.id} className='audience-step__arm-row'>
              <span
                className='audience-step__arm-dot'
                style={{ background: arm.colour }}
              />
              <span className='audience-step__arm-name'>{arm.name}</span>
              <div className='audience-step__arm-input'>
                <input
                  type='number'
                  min={0}
                  max={100}
                  value={getWeight(audience.weights, arm.id)}
                  onChange={(e) => handleWeightChange(arm.id, e.target.value)}
                />
                <span>%</span>
              </div>
            </div>
          ))}
        </div>

        <div className='audience-step__bar'>
          {arms.map((arm) => {
            const w = getWeight(audience.weights, arm.id)
            if (w === 0) return null
            return (
              <div
                key={arm.id}
                className='audience-step__bar-segment'
                style={{ background: arm.colour, width: `${w}%` }}
                title={`${arm.name}: ${w}%`}
              />
            )
          })}
        </div>
      </section>

      <div className='audience-step__sample-estimate'>
        <Icon name='people' width={20} />
        <span>
          {selectedSegment ? (
            <>
              <strong>{selectedSegment.label}</strong> has{' '}
              {eligibleUsers.toLocaleString()} eligible users.{' '}
            </>
          ) : (
            <>
              {eligibleUsers.toLocaleString()} eligible users in this
              environment.{' '}
            </>
          )}
          Sampling {audience.samplePercentage}% (~
          {sampledUsers.toLocaleString()}) into the experiment, split as{' '}
          {armEstimates
            .filter((e) => getWeight(audience.weights, e.arm.id) > 0)
            .map((e, i, arr) => (
              <React.Fragment key={e.arm.id}>
                {i > 0 && (i === arr.length - 1 ? ' and ' : ', ')}
                <strong>{e.arm.name}</strong> ~{e.users.toLocaleString()}
              </React.Fragment>
            ))}
          . Actual time-to-significance depends on traffic, baseline rate, and
          the lift you&apos;re trying to detect.
        </span>
      </div>
    </div>
  )
}

AudienceStep.displayName = 'AudienceStep'
export default AudienceStep
