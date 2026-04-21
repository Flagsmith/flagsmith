import React, { FC, useMemo } from 'react'
import Banner from 'components/Banner/Banner'
import EmptyState from 'components/EmptyState'
import SearchableSelect from 'components/base/select/SearchableSelect'
import VariationTable from 'components/experiments-v2/shared/VariationTable'
import { OptionType } from 'components/base/select/SearchableSelect'
import {
  MIN_VARIATIONS_FOR_EXPERIMENT,
  MOCK_FLAGS,
  Variation,
} from 'components/experiments-v2/types'
import './FlagVariationsStep.scss'

type FlagVariationsStepProps = {
  featureFlagId: string | null
  controlValue: string
  variations: Variation[]
  onFlagChange: (flagId: string) => void
  onControlValueChange: (value: string) => void
  onVariationsChange: (variations: Variation[]) => void
}

const FlagVariationsStep: FC<FlagVariationsStepProps> = ({
  controlValue,
  featureFlagId,
  onControlValueChange,
  onFlagChange,
  onVariationsChange,
  variations,
}) => {
  const eligibleFlags = useMemo(
    () => MOCK_FLAGS.filter((f) => f.isMultiVariant),
    [],
  )

  if (eligibleFlags.length === 0) {
    return (
      <div className='flag-variations-step'>
        <EmptyState
          title='No multi-variant flags'
          description='Experiments require a multi-variant feature flag. Create one first, then come back to set up your experiment.'
          icon='features'
        />
      </div>
    )
  }

  const handleFlagChange = (flagId: string) => {
    onFlagChange(flagId)
    const flag = MOCK_FLAGS.find((f) => f.value === flagId)
    onControlValueChange(flag?.controlValue ?? '')
    onVariationsChange(flag?.variations ?? [])
  }

  const selectedFlag = eligibleFlags.find((f) => f.value === featureFlagId)

  const hasInsufficientVariations =
    !!featureFlagId && variations.length < MIN_VARIATIONS_FOR_EXPERIMENT

  return (
    <div className='flag-variations-step'>
      <div className='flag-variations-step__field'>
        <label className='flag-variations-step__label'>Feature Flag</label>
        <SearchableSelect
          value={featureFlagId}
          displayedLabel={selectedFlag?.label}
          onChange={(opt: OptionType) => handleFlagChange(opt.value)}
          options={eligibleFlags}
          placeholder='Select a feature flag...'
        />
        <span className='flag-variations-step__hint text-muted fs-small'>
          Only multi-variant flags can be experimented on.
        </span>
      </div>

      {hasInsufficientVariations && (
        <Banner variant='warning'>
          <span>
            This flag has no variations beyond the control value. Experiments
            need at least {MIN_VARIATIONS_FOR_EXPERIMENT} variation to run — add
            one on the flag page to make it eligible.
          </span>
        </Banner>
      )}

      <div className='flag-variations-step__field'>
        <label className='flag-variations-step__label'>Variations</label>
        {featureFlagId ? (
          <VariationTable controlValue={controlValue} variations={variations} />
        ) : (
          <div className='flag-variations-step__no-variations'>
            <EmptyState
              title='Select a flag to see its variations'
              description='Variations are defined on the feature flag and cannot be edited from here.'
              icon='layers'
            />
          </div>
        )}
      </div>
    </div>
  )
}

FlagVariationsStep.displayName = 'FlagVariationsStep'
export default FlagVariationsStep
