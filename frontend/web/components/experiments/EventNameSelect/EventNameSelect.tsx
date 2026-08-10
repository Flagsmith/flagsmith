import { FC, useMemo, useState } from 'react'
import CreatableSelect from 'react-select/creatable'
import { InputActionMeta } from 'react-select'
import {
  useGetWarehouseConnectionEventsQuery,
  useGetWarehouseConnectionsQuery,
} from 'common/services/useWarehouseConnection'
import { WarehouseType } from 'common/types/responses'
import { useRouteContext } from 'components/providers/RouteContext'
import Icon from 'components/icons/Icon'
import { buildEventOptions, EventOption, isUnknownEvent } from './utils'
import './EventNameSelect.scss'

type EventNameSelectProps = {
  value: string
  onChange: (value: string) => void
}

const SUPPORTED_WAREHOUSE_TYPES: WarehouseType[] = ['flagsmith', 'clickhouse']

const EventNameSelect: FC<EventNameSelectProps> = ({ onChange, value }) => {
  const { environmentId } = useRouteContext()
  const { data: connections } = useGetWarehouseConnectionsQuery(
    { environmentId: environmentId ?? '', exclude_event_stats: true },
    { skip: !environmentId },
  )
  const connection = connections?.[0]
  const canListEvents =
    !!connection &&
    SUPPORTED_WAREHOUSE_TYPES.includes(connection.warehouse_type)
  const { data, isLoading, isSuccess } = useGetWarehouseConnectionEventsQuery(
    { environmentId: environmentId ?? '', id: connection?.id ?? 0 },
    { skip: !environmentId || !canListEvents },
  )
  const options = useMemo(() => buildEventOptions(data?.events), [data?.events])
  const showWarning = isSuccess && isUnknownEvent(value, data?.events)
  const [inputValue, setInputValue] = useState('')

  // Keep the typed text on blur (react-select discards it by default) so
  // clicking outside commits the value instead of clearing it.
  const handleInputChange = (val: string, meta: InputActionMeta) => {
    if (meta.action === 'input-change') setInputValue(val)
    if (meta.action === 'set-value') setInputValue('')
  }
  const handleBlur = () => {
    if (!inputValue) return
    onChange(inputValue)
    setInputValue('')
  }

  return (
    <div className='event-name-select'>
      <CreatableSelect
        inputId='metric-event'
        className='react-select'
        classNamePrefix='react-select'
        isClearable
        isLoading={isLoading}
        inputValue={inputValue}
        onInputChange={handleInputChange}
        onBlur={handleBlur}
        maxMenuHeight={200}
        menuPlacement='auto'
        options={options}
        value={value ? { label: value, value } : null}
        onChange={(option: EventOption | null) => onChange(option?.value ?? '')}
        placeholder='e.g. checkout_completed'
        formatCreateLabel={(input: string) => `Use "${input}"`}
        noOptionsMessage={() => 'Type to add a new event'}
      />
      {showWarning && (
        <span className='d-flex align-items-center gap-1 text-warning fs-small mt-1'>
          <Icon name='warning' width={14} className='text-warning' />
          This event hasn&apos;t been received by your warehouse yet.
        </span>
      )}
    </div>
  )
}

EventNameSelect.displayName = 'EventNameSelect'
export default EventNameSelect
