import React, { FC, useState } from 'react'
import Button from 'components/base/forms/Button'
import Input from 'components/base/forms/Input'
import {
  MeasurementType,
  Metric,
  MetricDirection,
} from 'components/experiments-v2/types'
import './CreateMetricForm.scss'

type CreateMetricFormProps = {
  initialValues?: Metric
  onCancel: () => void
  onSubmit: (metric: Metric) => void
}

const MEASUREMENT_OPTIONS: {
  value: MeasurementType
  title: string
  description: string
  example: string
}[] = [
  {
    description: 'Number of times an event occurred',
    example: 'ex: Number of purchases made',
    title: 'Count',
    value: 'count',
  },
  {
    description: 'Whether an event is seen at least once',
    example: 'ex: Signup completion',
    title: 'Occurrence',
    value: 'occurrence',
  },
  {
    description: 'Magnitude of an event with an associated number',
    example: 'ex: Latency or purchase value',
    title: 'Value / Size',
    value: 'value',
  },
]

const DIRECTION_OPTIONS: { value: MetricDirection; label: string }[] = [
  { label: 'Higher is better', value: 'higher-better' },
  { label: 'Lower is better', value: 'lower-better' },
  { label: 'Neither — informational only', value: 'neither' },
]

const CreateMetricForm: FC<CreateMetricFormProps> = ({
  initialValues,
  onCancel,
  onSubmit,
}) => {
  const isEdit = !!initialValues
  const [name, setName] = useState(initialValues?.name ?? '')
  const [description, setDescription] = useState(
    initialValues?.description ?? '',
  )
  const [measurementType, setMeasurementType] = useState<MeasurementType>(
    initialValues?.measurementType ?? 'occurrence',
  )
  const [direction, setDirection] = useState<MetricDirection>(
    initialValues?.direction ?? 'higher-better',
  )

  const canSubmit = name.trim().length > 0 && description.trim().length > 0

  const handleSubmit = () => {
    if (!canSubmit) return
    if (initialValues) {
      onSubmit({
        ...initialValues,
        description: description.trim(),
        direction,
        lastUpdated: 'Just now',
        measurementType,
        name: name.trim(),
      })
    } else {
      onSubmit({
        description: description.trim(),
        direction,
        id: `metric-${Date.now()}`,
        lastUpdated: 'Just now',
        measurementType,
        name: name.trim(),
        role: 'secondary',
        usageCount: 0,
      })
    }
  }

  return (
    <div className='create-metric-form'>
      <div className='create-metric-form__header'>
        <span className='create-metric-form__title'>
          {isEdit ? 'Edit Metric' : 'Create Metric'}
        </span>
        <span className='create-metric-form__subtitle'>
          Metrics capture the outcomes your experiments measure.
        </span>
      </div>

      <div className='create-metric-form__field'>
        <label className='create-metric-form__label' htmlFor='metric-name'>
          Name
        </label>
        <Input
          id='metric-name'
          value={name}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setName(e.target.value)
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
          value={description}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setDescription(e.target.value)
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
            <button
              key={opt.value}
              type='button'
              className={`create-metric-form__measurement-card ${
                measurementType === opt.value
                  ? 'create-metric-form__measurement-card--selected'
                  : ''
              }`}
              onClick={() => setMeasurementType(opt.value)}
            >
              <span className='create-metric-form__measurement-title'>
                {opt.title}
              </span>
              <span className='create-metric-form__measurement-desc'>
                {opt.description}
              </span>
              <span className='create-metric-form__measurement-ex'>
                {opt.example}
              </span>
            </button>
          ))}
        </div>
      </div>

      <div className='create-metric-form__field'>
        <label className='create-metric-form__label'>Direction</label>
        <div className='create-metric-form__direction-group'>
          {DIRECTION_OPTIONS.map((opt) => (
            <label
              key={opt.value}
              className={`create-metric-form__direction-pill ${
                direction === opt.value
                  ? 'create-metric-form__direction-pill--selected'
                  : ''
              }`}
            >
              <input
                type='radio'
                name='metric-direction'
                value={opt.value}
                checked={direction === opt.value}
                onChange={() => setDirection(opt.value)}
              />
              {opt.label}
            </label>
          ))}
        </div>
      </div>

      <div className='create-metric-form__actions'>
        <Button theme='outline' size='small' onClick={onCancel}>
          Cancel
        </Button>
        <Button
          theme='primary'
          size='small'
          onClick={handleSubmit}
          disabled={!canSubmit}
        >
          {isEdit ? 'Save Changes' : 'Create Metric'}
        </Button>
      </div>
    </div>
  )
}

CreateMetricForm.displayName = 'CreateMetricForm'
export default CreateMetricForm
