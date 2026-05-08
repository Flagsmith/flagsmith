import React, { FC, useMemo } from 'react'
import Banner from 'components/Banner/Banner'
import EmptyState from 'components/EmptyState'
import Input from 'components/base/forms/Input'
import SearchableSelect, {
  OptionType,
} from 'components/base/select/SearchableSelect'
import VariationTable from 'components/experiments-v2/shared/VariationTable'
import {
  ExperimentDetails,
  MIN_VARIATIONS_FOR_EXPERIMENT,
  MOCK_FLAGS,
  Variation,
} from 'components/experiments-v2/types'
import './SetupStep.scss'

type SetupStepProps = {
  details: ExperimentDetails
  featureFlagId: string | null
  controlValue: string
  variations: Variation[]
  onDetailsChange: (details: ExperimentDetails) => void
  onFlagChange: (flagId: string) => void
  onControlValueChange: (value: string) => void
  onVariationsChange: (variations: Variation[]) => void
}

const SetupStep: FC<SetupStepProps> = ({
  controlValue,
  details,
  featureFlagId,
  onControlValueChange,
  onDetailsChange,
  onFlagChange,
  onVariationsChange,
  variations,
}) => {
  const eligibleFlags = useMemo(
    () => MOCK_FLAGS.filter((f) => f.isMultiVariant),
    [],
  )

  const handleFlagChange = (flagId: string) => {
    onFlagChange(flagId)
    const flag = MOCK_FLAGS.find((f) => f.value === flagId)
    onControlValueChange(flag?.controlValue ?? '')
    onVariationsChange(flag?.variations ?? [])
  }

  const selectedFlag = eligibleFlags.find((f) => f.value === featureFlagId)

  const hasInsufficientVariations =
    !!featureFlagId && variations.length < MIN_VARIATIONS_FOR_EXPERIMENT

  const collidingVariations = useMemo(
    () =>
      variations.filter(
        (v) => v.value.trim().length > 0 && v.value === controlValue,
      ),
    [variations, controlValue],
  )

  const segmentOverrides = selectedFlag?.existingSegmentOverrides ?? []

  return (
    <div className='setup-step'>
      <section className='setup-step__section'>
        <h3 className='setup-step__section-title'>Experiment details</h3>
        <p className='setup-step__section-hint text-muted fs-small'>
          Name the experiment and capture what you're trying to learn before
          picking a flag.
        </p>

        <div className='setup-step__field'>
          <label className='setup-step__label'>
            Experiment Name <span className='setup-step__required'>*</span>
          </label>
          <Input
            value={details.name}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              onDetailsChange({ ...details, name: e.target.value })
            }
            placeholder='e.g. Checkout Flow Redesign'
          />
        </div>

        <div className='setup-step__field'>
          <label className='setup-step__label'>
            Hypothesis <span className='setup-step__required'>*</span>
          </label>
          <textarea
            className='setup-step__textarea'
            value={details.hypothesis}
            onChange={(e) =>
              onDetailsChange({ ...details, hypothesis: e.target.value })
            }
            placeholder='e.g. Switching to a one-click checkout will increase completion rate by at least 10% within 30 days.'
            rows={3}
          />
          <span className='setup-step__hint text-muted fs-small'>
            A good hypothesis names the change, the metric, the expected
            magnitude, and the timeframe.
          </span>
        </div>

        <div className='setup-step__date-row'>
          <div className='setup-step__field'>
            <label className='setup-step__label'>Start date</label>
            <Input
              type='date'
              value={details.startDate}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                onDetailsChange({ ...details, startDate: e.target.value })
              }
            />
          </div>
          <div className='setup-step__field'>
            <label className='setup-step__label'>End date</label>
            <Input
              type='date'
              value={details.endDate}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                onDetailsChange({ ...details, endDate: e.target.value })
              }
            />
          </div>
        </div>
      </section>

      <section className='setup-step__section'>
        <h3 className='setup-step__section-title'>Feature flag</h3>
        <p className='setup-step__section-hint text-muted fs-small'>
          The flag you're experimenting on. Variations are read-only — they're
          defined on the flag itself.
        </p>

        {eligibleFlags.length === 0 ? (
          <EmptyState
            title='No multi-variant flags'
            description='Experiments require a multi-variant feature flag. Create one first, then come back to set up your experiment.'
            icon='features'
          />
        ) : (
          <>
            <div className='setup-step__field'>
              <label className='setup-step__label'>Feature Flag</label>
              <SearchableSelect
                value={featureFlagId}
                displayedLabel={selectedFlag?.label}
                onChange={(opt: OptionType) => handleFlagChange(opt.value)}
                options={eligibleFlags}
                placeholder='Select a feature flag…'
              />
              <span className='setup-step__hint text-muted fs-small'>
                Only multi-variant flags can be experimented on.
              </span>
            </div>

            {hasInsufficientVariations && (
              <Banner variant='warning'>
                <span>
                  This flag has no variations beyond the control value.
                  Experiments need at least {MIN_VARIATIONS_FOR_EXPERIMENT}{' '}
                  variation to run — add one on the flag page to make it
                  eligible.
                </span>
              </Banner>
            )}

            {collidingVariations.length > 0 && (
              <Banner variant='warning'>
                <span>
                  {collidingVariations.length === 1 ? (
                    <>
                      Variation <strong>{collidingVariations[0].name}</strong>{' '}
                      serves the same value as control (
                      <code>{controlValue}</code>).
                    </>
                  ) : (
                    <>
                      <strong>{collidingVariations.length} variations</strong>{' '}
                      serve the same value as control (
                      <code>{controlValue}</code>).
                    </>
                  )}{' '}
                  Identities bucketed into{' '}
                  {collidingVariations.length === 1 ? 'it' : 'them'} will be
                  indistinguishable from control at evaluation time — fix the
                  values on the flag before launching.
                </span>
              </Banner>
            )}

            {segmentOverrides.length > 0 && (
              <Banner variant='warning'>
                <span>
                  This flag has{' '}
                  <strong>
                    {segmentOverrides.length} segment override
                    {segmentOverrides.length === 1 ? '' : 's'}
                  </strong>
                  :{' '}
                  {segmentOverrides.map((o) => `${o.segmentLabel}`).join(', ')}.
                  Users matching{' '}
                  {segmentOverrides.length === 1
                    ? 'this segment'
                    : 'these segments'}{' '}
                  will continue receiving their override variant and{' '}
                  <strong>will not enter the experiment</strong>.
                </span>
              </Banner>
            )}

            <div className='setup-step__field'>
              <label className='setup-step__label'>Variations</label>
              {featureFlagId ? (
                <VariationTable
                  controlValue={controlValue}
                  variations={variations}
                />
              ) : (
                <div className='setup-step__no-variations'>
                  <EmptyState
                    title='Select a flag to see its variations'
                    description='Variations are defined on the feature flag and cannot be edited from here.'
                    icon='layers'
                  />
                </div>
              )}
            </div>
          </>
        )}
      </section>
    </div>
  )
}

SetupStep.displayName = 'SetupStep'
export default SetupStep
