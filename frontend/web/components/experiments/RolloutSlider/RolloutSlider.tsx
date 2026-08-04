import { ChangeEvent, FC } from 'react'
import { colorSurfaceEmphasis, colorTextAction } from 'common/theme/tokens'
import Input from 'components/base/forms/Input'
import Utils from 'common/utils/utils'
import './RolloutSlider.scss'

type RolloutSliderProps = {
  value: number
  onChange: (value: number) => void
}

const TICKS = [0, 25, 50, 75, 100]

const clamp = (value: number): number => Math.min(100, Math.max(0, value))

const RolloutSlider: FC<RolloutSliderProps> = ({ onChange, value }) => {
  const fill = `linear-gradient(to right, ${colorTextAction} ${value}%, ${colorSurfaceEmphasis} ${value}%)`

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const parsed = parseInt(Utils.safeParseEventValue(e), 10)
    onChange(clamp(Number.isNaN(parsed) ? 0 : parsed))
  }

  return (
    <div className='rollout-slider'>
      <div className='rollout-slider__field'>
        <Input
          type='number'
          size='small'
          underline
          min={0}
          max={100}
          value={value}
          onChange={handleInputChange}
          inputClassName='rollout-slider__field-input'
          aria-label='Rollout percentage'
        />
        <span className='rollout-slider__field-suffix'>%</span>
      </div>

      <div className='rollout-slider__row'>
        <div className='rollout-slider__track'>
          <input
            type='range'
            min={0}
            max={100}
            step={1}
            value={value}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              onChange(Number(e.target.value))
            }
            className='rollout-slider__input'
            style={{ background: fill }}
            aria-label='Rollout percentage'
          />
          <div className='rollout-slider__ticks'>
            {TICKS.map((tick) => (
              <button
                type='button'
                key={tick}
                className='rollout-slider__tick'
                style={{ left: `${tick}%` }}
                onClick={() => onChange(tick)}
                aria-label={`Set rollout to ${tick} percent`}
              >
                <span className='rollout-slider__tick-mark' />
                <span className='rollout-slider__tick-label'>{tick}%</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default RolloutSlider
