import { FC } from 'react'
import { useHistory } from 'react-router-dom'
import moment from 'moment'
import { Experiment } from 'common/types/responses'
import StatusBadge from 'components/experiments/StatusBadge'
import ExperimentActionDropdown from 'components/experiments/ExperimentActionDropdown'
import { getPrimaryMetric } from 'components/experiments/constants'
import './ExperimentsTable.scss'

type ExperimentsTableProps = {
  experiments: Experiment[]
  environmentId: string
  projectId: number
}

const ExperimentsTable: FC<ExperimentsTableProps> = ({
  environmentId,
  experiments,
  projectId,
}) => {
  const history = useHistory()
  return (
    <table className='experiments-table'>
      <thead>
        <tr>
          <th>Experiment Name</th>
          <th>Linked Flag</th>
          <th>Status</th>
          <th>Variations</th>
          <th>Primary Metric</th>
          <th>Last Updated</th>
          <th />
        </tr>
      </thead>
      <tbody>
        {experiments.map((exp) => {
          const primaryMetric = getPrimaryMetric(exp)
          return (
            <tr
              key={exp.id}
              className='experiments-table__row experiments-table__row--clickable'
              onClick={() =>
                history.push(
                  `/project/${projectId}/environment/${environmentId}/experiments/${exp.id}`,
                )
              }
            >
              <td className='fw-medium'>{exp.name}</td>
              <td>
                {exp.feature?.name && (
                  <code className='experiments-table__flag-name'>
                    {exp.feature.name}
                  </code>
                )}
              </td>
              <td>
                <StatusBadge status={exp.status} />
              </td>
              <td>{(exp.feature?.multivariate_options?.length ?? 0) + 1}</td>
              <td className='text-muted'>
                {primaryMetric?.metric_name ?? <>&mdash;</>}
              </td>
              <td className='text-muted'>{moment(exp.updated_at).fromNow()}</td>
              <td
                className='experiments-table__actions'
                onClick={(e) => e.stopPropagation()}
              >
                <ExperimentActionDropdown
                  experimentId={exp.id}
                  experimentName={exp.name}
                  status={exp.status}
                  environmentId={environmentId}
                />
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}

export default ExperimentsTable
