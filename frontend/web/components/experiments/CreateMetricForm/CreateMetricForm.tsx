import React, { FC, useState } from 'react'
import Button from 'components/base/forms/Button'
import Input from 'components/base/forms/Input'
import {
  canSubmitMetric,
  DEFAULT_METRIC_FORM_STATE,
  DIRECTION_OPTIONS,
  MEASUREMENT_OPTIONS,
  MetricFormState,
} from './utils'
import './CreateMetricForm.scss'

type CreateMetricFormProps = {
  initialState?: MetricFormState
  isSaving?: boolean
  submitLabel?: string
  onCancel: () => void
  onSubmit: (state: MetricFormState) => void
}

const CreateMetricForm: FC<CreateMetricFormProps> = ({
  initialState = DEFAULT_METRIC_FORM_STATE,
  isSaving,
  onCancel,
  onSubmit,
  submitLabel = 'Create Metric',
}) => {
  const [state, setState] = useState<MetricFormState>(initialState)

  const update = (patch: Partial<MetricFormState>) =>
    setState((prev) => ({ ...prev, ...patch }))

  const handleCancel = () => {
    setState(initialState)
    onCancel()
  }

  const handleSubmit = () => {
    if (!canSubmitMetric(state) || isSaving) return
    onSubmit(state)
  }

  return (
    <div className='create-metric-form d-flex flex-column gap-4'>
      <div className='create-metric-form__field'>
        <label className='create-metric-form__label' htmlFor='metric-name'>
          Name
        </label>
        <Input
          id='metric-name'
          value={state.name}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            update({ name: e.target.value })
          }
          placeholder='e.g. Signup Completion Rate'
        />
      </div>

      <div className='create-metric-form__field'>
        <label
          className='create-metric-form__label'
          htmlFor='metric-description'
        >
          Description
        </label>
        <Input
          id='metric-description'
          value={state.description}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            update({ description: e.target.value })
          }
          placeholder='What does this metric measure?'
        />
      </div>

      <div className='create-metric-form__field'>
        <label className='create-metric-form__label'>
          What do you want to measure?
        </label>
        <div className='create-metric-form__measurement-grid'>
          {MEASUREMENT_OPTIONS.map((opt) => (
            <label
              key={opt.value}
              className={`create-metric-form__measurement-card ${
                state.aggregation === opt.value
                  ? 'create-metric-form__measurement-card--selected'
                  : ''
              }`}
            >
              <input
                type='radio'
                name='metric-aggregation'
                value={opt.value}
                checked={state.aggregation === opt.value}
                onChange={() => update({ aggregation: opt.value })}
              />
              <span className='create-metric-form__measurement-head'>
                <span className='create-metric-form__measurement-title'>
                  {opt.title}
                </span>
                <span className='create-metric-form__measurement-desc'>
                  {opt.description}
                </span>
              </span>
              <span className='create-metric-form__measurement-ex'>
                {opt.example}
              </span>
            </label>
          ))}
        </div>
      </div>

      <div className='create-metric-form__field'>
        <label className='create-metric-form__label'>Direction</label>
        <div className='create-metric-form__direction-group d-flex flex-wrap gap-2'>
          {DIRECTION_OPTIONS.map((opt) => (
            <label
              key={opt.value}
              className={`create-metric-form__direction-pill ${
                state.direction === opt.value
                  ? 'create-metric-form__direction-pill--selected'
                  : ''
              }`}
            >
              <input
                type='radio'
                name='metric-direction'
                value={opt.value}
                checked={state.direction === opt.value}
                onChange={() => update({ direction: opt.value })}
              />
              {opt.label}
            </label>
          ))}
        </div>
      </div>

      <div className='create-metric-form__field'>
        <label className='create-metric-form__label'>Data Source</label>
        <span className='create-metric-form__hint text-muted fs-small'>
          Where this metric is collected from. Reads from your connected
          warehouse.
        </span>
        <div className='create-metric-form__source gap-3 p-3 rounded-md bg-surface-subtle'>
          <div className='create-metric-form__source-col'>
            <label
              className='create-metric-form__sublabel'
              htmlFor='metric-event'
            >
              Event name
            </label>
            <Input
              id='metric-event'
              value={state.event}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                update({ event: e.target.value })
              }
              placeholder='e.g. checkout_completed'
            />
          </div>
        </div>
      </div>

      <div className='create-metric-form__actions d-flex justify-content-end gap-2 pt-2'>
        <Button
          id='metric-form-cancel'
          theme='outline'
          onClick={handleCancel}
          disabled={isSaving}
        >
          Cancel
        </Button>
        <Button
          id='metric-form-submit'
          theme='primary'
          onClick={handleSubmit}
          disabled={!canSubmitMetric(state) || isSaving}
        >
          {isSaving ? 'Saving…' : submitLabel}
        </Button>
      </div>
    </div>
  )
}

CreateMetricForm.displayName = 'CreateMetricForm'
export default CreateMetricForm
