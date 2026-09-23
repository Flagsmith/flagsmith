import { FC } from 'react'
import moment from 'moment'
import { Metric } from 'common/types/responses'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import {
  getMetricSubline,
  getMetricUsageLabel,
} from 'components/experiments/CreateMetricForm/utils'
import './MetricsTable.scss'

type MetricsTableProps = {
  metrics: Metric[]
  onEdit: (metric: Metric) => void
  onDelete: (metric: Metric) => void
}

const MetricsTable: FC<MetricsTableProps> = ({ metrics, onDelete, onEdit }) => {
  return (
    <table className='metrics-table'>
      <thead>
        <tr>
          <th>Name</th>
          <th>Description</th>
          <th>Used in</th>
          <th>Last updated</th>
          <th />
        </tr>
      </thead>
      <tbody>
        {metrics.map((metric) => (
          <tr key={metric.id} className='metrics-table__row'>
            <td>
              <span className='metrics-table__name'>{metric.name}</span>
              <span className='metrics-table__subline'>
                <Icon
                  name='layers'
                  width={14}
                  className='metrics-table__subline-icon'
                />
                {getMetricSubline(metric)}
              </span>
            </td>
            <td className='text-muted'>{metric.description || '—'}</td>
            <td className='text-muted'>
              {getMetricUsageLabel(metric.experiments?.length ?? 0)}
            </td>
            <td className='text-muted'>
              {moment(metric.updated_at).fromNow()}
            </td>
            <td className='metrics-table__actions'>
              <Button
                id={`metrics-table-edit-${metric.id}`}
                type='button'
                size='small'
                className='btn btn-with-icon'
                onClick={() => onEdit(metric)}
              >
                <Icon name='edit' width={16} fill='#656D7B' />
              </Button>
              <Button
                id={`metrics-table-delete-${metric.id}`}
                type='button'
                size='small'
                className='btn btn-with-icon'
                onClick={() => onDelete(metric)}
              >
                <Icon name='trash-2' width={16} fill='#656D7B' />
              </Button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export default MetricsTable
