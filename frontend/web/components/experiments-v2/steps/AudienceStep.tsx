import React, { FC, useMemo } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import AudienceConditionBuilder from 'components/experiments-v2/shared/AudienceConditionBuilder'
import {
  ArmWeight,
  AudienceCondition,
  AudienceConfig,
  CONTROL_ARM_ID,
  CONTROL_COLOUR,
  FlagOption,
  Layer,
  MOCK_ENVIRONMENT_USER_COUNT,
  MOCK_LAYERS,
  RANDOMISATION_UNIT_HINTS,
  RANDOMISATION_UNIT_LABELS,
  RandomisationUnit,
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
  /** Used to compute the override-excluded user count. */
  flag: FlagOption | null
  controlValue: string
  variations: Variation[]
  environmentName: string
  randomisationUnit: RandomisationUnit
  persistAcrossAuth: boolean
  layerId: string | null
  onChange: (audience: AudienceConfig) => void
  onRandomisationUnitChange: (unit: RandomisationUnit) => void
  onPersistAcrossAuthChange: (persist: boolean) => void
  onLayerIdChange: (layerId: string | null) => void
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
  layerId,
  onChange,
  onLayerIdChange,
  onPersistAcrossAuthChange,
  onRandomisationUnitChange,
  persistAcrossAuth,
  randomisationUnit,
  variations,
}) => {
  const selectedLayer: Layer | undefined = MOCK_LAYERS.find(
    (l) => l.value === layerId,
  )
  const arms = useMemo(
    () => buildExperimentArms(controlValue, variations),
    [controlValue, variations],
  )

  const handleConditionsChange = (conditions: AudienceCondition[]) => {
    onChange({ ...audience, conditions })
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

  // Mock estimate: if there are no conditions we use the full environment;
  // otherwise we apply a deterministic dampener so the number changes as
  // conditions grow. In production this would come from a real query.
  const eligibleUsers = useMemo(() => {
    if (audience.conditions.length === 0) return MOCK_ENVIRONMENT_USER_COUNT
    const dampener = Math.pow(0.55, audience.conditions.length)
    return Math.round(MOCK_ENVIRONMENT_USER_COUNT * dampener)
  }, [audience.conditions.length])

  // Approximate users excluded by flag-level segment overrides. In production
  // we'd intersect each override's segment with the audience to get the real
  // overlap; here we use a fixed mock factor per override.
  const overrideExcludedUsers = useMemo(() => {
    const overrideCount = flag?.existingSegmentOverrides.length ?? 0
    if (overrideCount === 0) return 0
    const excludedFraction = Math.min(0.5, overrideCount * 0.1)
    return Math.round(eligibleUsers * excludedFraction)
  }, [flag, eligibleUsers])

  const effectiveAudienceUsers = Math.max(
    0,
    eligibleUsers - overrideExcludedUsers,
  )

  const sampledUsers = Math.round(
    (effectiveAudienceUsers * audience.samplePercentage) / 100,
  )

  const armEstimates = arms.map((a) => ({
    arm: a,
    users: Math.round((sampledUsers * getWeight(audience.weights, a.id)) / 100),
  }))

  const isCustomSamplePercentage = !SAMPLE_SIZE_PRESETS.includes(
    audience.samplePercentage as (typeof SAMPLE_SIZE_PRESETS)[number],
  )

  const hasConditions = audience.conditions.length > 0

  return (
    <div className='audience-step'>
      <div className='audience-step__env'>
        <div className='audience-step__env-item'>
          <span className='audience-step__env-label'>Environment</span>
          <span className='audience-step__env-value'>{environmentName}</span>
        </div>
      </div>

      <section className='audience-step__section'>
        <div className='audience-step__section-header'>
          <h4 className='audience-step__section-title'>
            Bucketing &amp; exclusion
          </h4>
        </div>
        <span className='audience-step__hint text-muted fs-small'>
          How users are deterministically assigned to a variation, and whether
          this experiment is exclusive with other experiments.
        </span>

        <div className='audience-step__bucketing-row'>
          <div className='audience-step__bucketing-field'>
            <label className='audience-step__bucketing-label'>
              Randomisation unit
            </label>
            <select
              className='audience-step__bucketing-select'
              value={randomisationUnit}
              onChange={(e) =>
                onRandomisationUnitChange(e.target.value as RandomisationUnit)
              }
            >
              {(
                Object.keys(RANDOMISATION_UNIT_LABELS) as RandomisationUnit[]
              ).map((unit) => (
                <option key={unit} value={unit}>
                  {RANDOMISATION_UNIT_LABELS[unit]}
                </option>
              ))}
            </select>
            <span className='audience-step__hint text-muted fs-small'>
              {RANDOMISATION_UNIT_HINTS[randomisationUnit]}
            </span>
          </div>

          <div className='audience-step__bucketing-field'>
            <label className='audience-step__bucketing-label'>
              Mutual exclusion layer
              <span className='audience-step__optional-badge'>Optional</span>
            </label>
            <select
              className='audience-step__bucketing-select'
              value={layerId ?? ''}
              onChange={(e) => onLayerIdChange(e.target.value || null)}
            >
              <option value=''>None — independent experiment</option>
              {MOCK_LAYERS.map((layer) => (
                <option key={layer.value} value={layer.value}>
                  {layer.label} ({layer.experimentCount} active)
                </option>
              ))}
            </select>
            {selectedLayer && (
              <span className='audience-step__hint text-muted fs-small'>
                {selectedLayer.description}
                {selectedLayer.experimentCount > 0 && (
                  <>
                    {' '}
                    {selectedLayer.experimentCount} active experiment
                    {selectedLayer.experimentCount === 1 ? '' : 's'} share this
                    layer — users in those won&apos;t enter this one.
                  </>
                )}
              </span>
            )}
          </div>
        </div>

        {randomisationUnit === 'identity' && (
          <label className='audience-step__checkbox-row'>
            <input
              type='checkbox'
              checked={persistAcrossAuth}
              onChange={(e) => onPersistAcrossAuthChange(e.target.checked)}
            />
            <span>
              <strong>Persist across authentication</strong>
              <span className='audience-step__hint text-muted fs-small d-block'>
                Keep the same variation when an anonymous user signs in. Falls
                back to the device ID before sign-in.
              </span>
            </span>
          </label>
        )}
      </section>

      <section className='audience-step__section'>
        <div className='audience-step__section-header'>
          <h4 className='audience-step__section-title'>
            Targeting
            <span className='audience-step__optional-badge'>Optional</span>
          </h4>
          {hasConditions && (
            <Button
              theme='text'
              size='xSmall'
              onClick={() => handleConditionsChange([])}
            >
              Clear all
            </Button>
          )}
        </div>
        <span className='audience-step__hint text-muted fs-small'>
          Define who is eligible for the experiment using attribute conditions.
          Conditions are AND-joined. Leave empty to run on all identities in the
          environment. Conditions are frozen at launch &mdash; later edits to
          existing Segments cannot drift the experiment audience.
        </span>
        <AudienceConditionBuilder
          conditions={audience.conditions}
          onChange={handleConditionsChange}
        />
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
          {hasConditions ? (
            <>
              ~{eligibleUsers.toLocaleString()} users match the targeting
              conditions.{' '}
            </>
          ) : (
            <>
              {eligibleUsers.toLocaleString()} eligible users in this
              environment.{' '}
            </>
          )}
          {overrideExcludedUsers > 0 && (
            <>
              ~{overrideExcludedUsers.toLocaleString()} excluded by flag-level
              segment overrides; effective audience ~
              {effectiveAudienceUsers.toLocaleString()}.{' '}
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
