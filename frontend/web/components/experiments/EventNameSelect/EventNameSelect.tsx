import { FC, useMemo } from 'react'
import CreatableSelect from 'react-select/creatable'
import {
  useGetWarehouseConnectionEventsQuery,
  useGetWarehouseConnectionsQuery,
} from 'common/services/useWarehouseConnection'
import { WarehouseType } from 'common/types/responses'
import { useRouteContext } from 'components/providers/RouteContext'
import Icon from 'components/icons/Icon'
import { buildEventOptions, EventOption, isUnknownEvent } from './utils'

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

  return (
    <>
      <CreatableSelect
        inputId='metric-event'
        className='react-select'
        classNamePrefix='react-select'
        isClearable
        isLoading={isLoading}
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
    </>
  )
}

EventNameSelect.displayName = 'EventNameSelect'
export default EventNameSelect
