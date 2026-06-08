import React, { FC, useRef } from 'react'
import Button from 'components/base/forms/Button'
import InputGroup from 'components/base/forms/InputGroup'
import StepShell from 'web/components/pages/onboarding-quickstart/components/StepShell'
import { FEATURE_PRESETS } from 'web/components/pages/onboarding-quickstart/data/presets'

export const PRESET_CUSTOM = '__custom__'

type FeatureStepProps = {
  customValue: string
  isSubmitting: boolean
  onBack: () => void
  onCustomChange: (value: string) => void
  onFinish: () => void
  onPresetChange: (preset: string) => void
  selectedPreset: string
}

const FeatureStep: FC<FeatureStepProps> = ({
  customValue,
  isSubmitting,
  onBack,
  onCustomChange,
  onFinish,
  onPresetChange,
  selectedPreset,
}) => {
  const isCustom = selectedPreset === PRESET_CUSTOM
  const isValid = isCustom ? !!customValue.trim() : !!selectedPreset

  // Roving tabindex across presets + the "Choose your own…" option.
  // Custom is logically the last option in the radiogroup.
  const optionKeys = [...FEATURE_PRESETS.map((p) => p.key), PRESET_CUSTOM]
  const optionRefs = useRef<(HTMLButtonElement | null)[]>([])
  const selectedIndex = optionKeys.indexOf(selectedPreset)
  const tabbableIndex = selectedIndex === -1 ? 0 : selectedIndex

  const handleKeyDown = (
    e: React.KeyboardEvent<HTMLButtonElement>,
    index: number,
  ) => {
    let nextIndex: number | null = null
    if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
      // First arrow press with no selection yet picks the focused option;
      // subsequent presses advance.
      nextIndex = selectedIndex === -1 ? index : (index + 1) % optionKeys.length
    } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
      nextIndex =
        selectedIndex === -1
          ? index
          : (index - 1 + optionKeys.length) % optionKeys.length
    } else if (e.key === 'Home') {
      nextIndex = 0
    } else if (e.key === 'End') {
      nextIndex = optionKeys.length - 1
    } else if (
      e.key === 'Enter' &&
      selectedIndex !== -1 &&
      isValid &&
      !isSubmitting
    ) {
      // Enter on a focused option with a valid selection finishes setup
      // — saves a Tab + Enter to reach the Finish button. Excludes the
      // case where 'Choose your own…' is picked but no name typed yet
      // (handled by `isValid` check).
      e.preventDefault()
      onFinish()
      return
    }
    if (nextIndex !== null) {
      e.preventDefault()
      onPresetChange(optionKeys[nextIndex])
      optionRefs.current[nextIndex]?.focus()
    }
  }

  return (
    <StepShell
      title='What feature are you working on?'
      subtitle="We'll create it as your first flag. Heads up — flags can't be renamed later; delete and recreate if you change your mind."
      body={
        <div
          role='radiogroup'
          aria-label='Feature preset'
          className='d-flex flex-column gap-2'
        >
          {FEATURE_PRESETS.map((preset, index) => {
            const isSelected = selectedPreset === preset.key
            return (
              <button
                ref={(el) => {
                  optionRefs.current[index] = el
                }}
                type='button'
                role='radio'
                aria-checked={isSelected}
                tabIndex={index === tabbableIndex ? 0 : -1}
                key={preset.key}
                onClick={() => onPresetChange(preset.key)}
                onKeyDown={(e) => handleKeyDown(e, index)}
                className={`onboarding-quickstart__radio-row w-100 text-start p-3 rounded-md border ${
                  isSelected
                    ? 'border-action bg-surface-action-subtle'
                    : 'border-default bg-surface-default'
                }`}
              >
                <span
                  className={`onboarding-quickstart__radio-dot ${
                    isSelected ? 'onboarding-quickstart__radio-dot--on' : ''
                  }`}
                  aria-hidden='true'
                />
                <span className='ms-2'>
                  <code className='text-default'>{preset.key}</code>
                  <span className='ms-2 text-muted'>
                    {preset.label.split('—').slice(1).join('—').trim()}
                  </span>
                </span>
              </button>
            )
          })}
          <button
            ref={(el) => {
              optionRefs.current[FEATURE_PRESETS.length] = el
            }}
            type='button'
            role='radio'
            aria-checked={isCustom}
            tabIndex={FEATURE_PRESETS.length === tabbableIndex ? 0 : -1}
            onClick={() => onPresetChange(PRESET_CUSTOM)}
            onKeyDown={(e) => handleKeyDown(e, FEATURE_PRESETS.length)}
            className={`onboarding-quickstart__radio-row w-100 text-start p-3 rounded-md border ${
              isCustom
                ? 'border-action bg-surface-action-subtle'
                : 'border-default bg-surface-default'
            }`}
          >
            <span
              className={`onboarding-quickstart__radio-dot ${
                isCustom ? 'onboarding-quickstart__radio-dot--on' : ''
              }`}
              aria-hidden='true'
            />
            <span className='ms-2 text-default'>Choose your own…</span>
          </button>
          {isCustom && (
            <div className='mt-2'>
              <InputGroup
                title='Custom feature name'
                placeholder='e.g. header_size'
                inputProps={{
                  name: 'customFeatureName',
                  onKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => {
                    if (e.key === 'Enter' && isValid && !isSubmitting) {
                      e.preventDefault()
                      onFinish()
                    }
                  },
                }}
                value={customValue}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  // Mirror the main app's feature-ID constraint: spaces are
                  // not allowed in a flag name — replace them with underscores
                  // as the user types (see FeatureNameInput in create-feature).
                  onCustomChange(e.target.value.replace(/ /g, '_'))
                }
                isValid={!!customValue}
              />
            </div>
          )}
        </div>
      }
      footer={
        <>
          <Button theme='text' onClick={onBack} disabled={isSubmitting}>
            ← Back
          </Button>
          <Button
            theme='primary'
            onClick={onFinish}
            disabled={!isValid || isSubmitting}
          >
            {isSubmitting ? 'Setting up…' : 'Finish setup →'}
          </Button>
        </>
      }
    />
  )
}

export default FeatureStep
