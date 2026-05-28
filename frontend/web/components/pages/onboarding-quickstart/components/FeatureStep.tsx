import React, { FC } from 'react'
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

  return (
    <StepShell
      title='What feature are you working on?'
      subtitle="We'll create it as your first flag. Heads up — flags can't be renamed later; delete and recreate if you change your mind."
      body={
        <div className='d-flex flex-column gap-2'>
          {FEATURE_PRESETS.map((preset) => {
            const isSelected = selectedPreset === preset.key
            return (
              <button
                type='button'
                key={preset.key}
                onClick={() => onPresetChange(preset.key)}
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
            type='button'
            onClick={() => onPresetChange(PRESET_CUSTOM)}
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
                inputProps={{ name: 'customFeatureName' }}
                value={customValue}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  onCustomChange(e.target.value)
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
