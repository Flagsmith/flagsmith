import React, { FC, useState } from 'react'
import Button from 'components/base/forms/Button'
import Input from 'components/base/forms/Input'
import {
  MeasurementType,
  Metric,
  MetricDirection,
  MetricSource,
} from 'components/experiments-v2/types'
import './CreateMetricForm.scss'

const WAREHOUSE_TABLES = [
  'EVENTS',
  'PAGE_VIEWS',
  'SESSIONS',
  'TRANSACTIONS',
  'USERS',
]

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
  const [sourceTable, setSourceTable] = useState<string>(
    initialValues?.source?.table ?? 'EVENTS',
  )
  const [sourceEventName, setSourceEventName] = useState<string>(
    initialValues?.source?.eventName ?? '',
  )
  const [sourceValueColumn, setSourceValueColumn] = useState<string>(
    initialValues?.source?.valueColumn ?? '',
  )
  const [sourceFilter, setSourceFilter] = useState<string>(
    initialValues?.source?.filter ?? '',
  )

  const canSubmit = name.trim().length > 0 && description.trim().length > 0

  const buildSource = (): MetricSource | undefined => {
    const table = sourceTable.trim()
    if (!table) return undefined
    const source: MetricSource = { table, warehouse: 'snowflake' }
    const needsEventName =
      measurementType === 'count' || measurementType === 'occurrence'
    if (needsEventName && sourceEventName.trim()) {
      source.eventName = sourceEventName.trim()
    }
    if (measurementType === 'value' && sourceValueColumn.trim()) {
      source.valueColumn = sourceValueColumn.trim()
    }
    if (sourceFilter.trim()) {
      source.filter = sourceFilter.trim()
    }
    return source
  }

  const handleSubmit = () => {
    if (!canSubmit) return
    const source = buildSource()
    if (initialValues) {
      onSubmit({
        ...initialValues,
        description: description.trim(),
        direction,
        lastUpdated: 'Just now',
        measurementType,
        name: name.trim(),
        source,
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
        source,
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

      <div className='create-metric-form__field'>
        <label className='create-metric-form__label'>Data Source</label>
        <span className='create-metric-form__hint text-muted fs-small'>
          Where this metric is collected from. Reads from your connected
          warehouse.
        </span>
        <div className='create-metric-form__source'>
          <div className='create-metric-form__source-row'>
            <div className='create-metric-form__source-col'>
              <label
                className='create-metric-form__sublabel'
                htmlFor='metric-source-warehouse'
              >
                Warehouse
              </label>
              <div
                className='create-metric-form__source-pill'
                id='metric-source-warehouse'
              >
                Snowflake &middot;{' '}
                <span className='create-metric-form__source-pill-path'>
                  FLAGSMITH_PROD.PUBLIC
                </span>
              </div>
            </div>
            <div className='create-metric-form__source-col'>
              <label
                className='create-metric-form__sublabel'
                htmlFor='metric-source-table'
              >
                Table
              </label>
              <select
                id='metric-source-table'
                className='create-metric-form__source-select'
                value={sourceTable}
                onChange={(e) => setSourceTable(e.target.value)}
              >
                {WAREHOUSE_TABLES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {(measurementType === 'count' ||
            measurementType === 'occurrence') && (
            <div className='create-metric-form__source-col'>
              <label
                className='create-metric-form__sublabel'
                htmlFor='metric-source-event'
              >
                Event name
              </label>
              <Input
                id='metric-source-event'
                value={sourceEventName}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setSourceEventName(e.target.value)
                }
                placeholder='e.g. checkout_completed'
              />
            </div>
          )}

          {measurementType === 'value' && (
            <div className='create-metric-form__source-col'>
              <label
                className='create-metric-form__sublabel'
                htmlFor='metric-source-column'
              >
                Value column
              </label>
              <Input
                id='metric-source-column'
                value={sourceValueColumn}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setSourceValueColumn(e.target.value)
                }
                placeholder='e.g. amount_usd'
              />
            </div>
          )}

          <div className='create-metric-form__source-col'>
            <label
              className='create-metric-form__sublabel'
              htmlFor='metric-source-filter'
            >
              Filter <span className='text-muted'>(optional)</span>
            </label>
            <Input
              id='metric-source-filter'
              value={sourceFilter}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setSourceFilter(e.target.value)
              }
              placeholder="e.g. status = 'complete'"
            />
          </div>
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
