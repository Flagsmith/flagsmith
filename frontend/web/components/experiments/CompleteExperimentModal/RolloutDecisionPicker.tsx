import { FC } from 'react'
import SelectableCard from 'components/base/SelectableCard'
import ColorSwatch from 'components/ColorSwatch'
import { VariantIdentity } from 'components/experiments/results/derive'
import VariantChoiceRow from './VariantChoiceRow'
import { RolloutSelection, VariantChoice } from './utils'

type VariantOption = {
  label: string
  value: number
  choice: VariantChoice
}

type RolloutDecisionPickerProps = {
  choices: VariantChoice[]
  control: VariantIdentity
  environmentName: string
  featureName: string
  selection: RolloutSelection
  onChange: (selection: RolloutSelection) => void
}

const RolloutDecisionPicker: FC<RolloutDecisionPickerProps> = ({
  choices,
  control,
  environmentName,
  featureName,
  onChange,
  selection,
}) => {
  const hasSingleChoice = choices.length === 1
  const variantOptions: VariantOption[] = choices.map((choice) => ({
    choice,
    label: choice.name,
    value: choice.optionId,
  }))

  return (
    <div className='d-flex flex-column gap-2 mx-0'>
      <SelectableCard
        selected={selection.decision === 'control'}
        onClick={() => onChange({ ...selection, decision: 'control' })}
        title={
          <span className='d-inline-flex align-items-center gap-2'>
            <ColorSwatch color={control.colour} shape='circle' size='sm' />
            Roll out control
          </span>
        }
        description={
          <>
            Everyone gets <code>{control.value}</code>.
          </>
        }
      />
      {!!choices.length && (
        <SelectableCard
          selected={selection.decision === 'variant'}
          onClick={() => onChange({ ...selection, decision: 'variant' })}
          title='Roll out a variant'
          description={
            hasSingleChoice
              ? 'Everyone gets the variant below.'
              : 'Everyone gets the chosen variant.'
          }
          footer={
            selection.decision === 'variant' &&
            !hasSingleChoice && (
              <Select
                aria-label='Variant'
                isSearchable={false}
                options={variantOptions}
                value={variantOptions.find(
                  (o) => o.value === selection.variantId,
                )}
                formatOptionLabel={(o: VariantOption) => (
                  <VariantChoiceRow choice={o.choice} />
                )}
                onChange={(o: VariantOption) =>
                  onChange({ decision: 'variant', variantId: o.value })
                }
              />
            )
          }
        >
          {hasSingleChoice && (
            <div className='mt-2'>
              <VariantChoiceRow choice={choices[0]} />
            </div>
          )}
        </SelectableCard>
      )}
      <SelectableCard
        selected={selection.decision === 'disable'}
        onClick={() => onChange({ ...selection, decision: 'disable' })}
        title='Turn the flag off'
        description={
          <>
            Disable <b>{featureName}</b> in {environmentName} for everyone.
          </>
        }
      />
    </div>
  )
}

export default RolloutDecisionPicker
