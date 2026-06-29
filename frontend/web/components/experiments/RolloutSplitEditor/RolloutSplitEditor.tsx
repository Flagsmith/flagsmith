import { ChangeEvent, FC } from 'react'
import { MultivariateOption } from 'common/types/responses'
import Input from 'components/base/forms/Input'
import ErrorMessage from 'components/ErrorMessage'
import ColorSwatch from 'components/ColorSwatch'
import Utils from 'common/utils/utils'
import { getDefaultVariantKey } from 'common/utils/multivariate'
import {
  CONTROL_COLOUR,
  VariationSplitEntry,
  getControlPercentage,
  getVariationColour,
} from 'components/experiments/rollout'
import './RolloutSplitEditor.scss'

type RolloutSplitEditorProps = {
  multivariateOptions: MultivariateOption[]
  variationSplit: VariationSplitEntry[]
  onChange: (entries: VariationSplitEntry[]) => void
}

const RolloutSplitEditor: FC<RolloutSplitEditorProps> = ({
  multivariateOptions,
  onChange,
  variationSplit,
}) => {
  const controlPercentage = getControlPercentage(variationSplit)
  const invalid = controlPercentage < 0 || controlPercentage > 100

  const getPercentage = (optionId: number): number =>
    variationSplit.find((v) => v.multivariate_feature_option === optionId)
      ?.percentage_allocation ?? 0

  const setPercentage = (optionId: number, percentage: number) =>
    onChange(
      variationSplit.map((entry) =>
        entry.multivariate_feature_option === optionId
          ? { ...entry, percentage_allocation: percentage }
          : entry,
      ),
    )

  return (
    <div className='rollout-split'>
      {invalid && (
        <ErrorMessage
          errorMessageClass='mb-2'
          error='Your variation percentage splits total to over 100%'
        />
      )}

      <div className='rollout-split__rows'>
        <div className='rollout-split__row'>
          <span className='rollout-split__name'>
            <ColorSwatch color={CONTROL_COLOUR} size='md' shape='circle' />
            <span className='rollout-split__name-text'>Control</span>
            <span className='rollout-split__control-tag'>control</span>
          </span>
          <span className='rollout-split__weight'>
            <Input
              type='number'
              size='small'
              centered
              readOnly
              value={Math.max(0, controlPercentage)}
            />
            <span className='text-muted'>%</span>
          </span>
        </div>

        {multivariateOptions.map((option, index) => (
          <div key={option.id} className='rollout-split__row'>
            <span className='rollout-split__name'>
              <ColorSwatch
                color={getVariationColour(index)}
                size='md'
                shape='circle'
              />
              <span className='rollout-split__name-text'>
                {option.key || getDefaultVariantKey(index)}
              </span>
            </span>
            <span className='rollout-split__weight'>
              <Input
                type='number'
                size='small'
                centered
                value={getPercentage(option.id)}
                step='any'
                onChange={(e: ChangeEvent<HTMLInputElement>) => {
                  const val = Utils.safeParseEventValue(e)
                  setPercentage(option.id, val ? parseFloat(val) : 0)
                }}
              />
              <span className='text-muted'>%</span>
            </span>
          </div>
        ))}
      </div>

      <p className='rollout-split__hint text-muted mb-0'>
        Bucketing is deterministic on the SDK identifier. The same identity
        always lands in the same variation.
      </p>
    </div>
  )
}

export default RolloutSplitEditor
