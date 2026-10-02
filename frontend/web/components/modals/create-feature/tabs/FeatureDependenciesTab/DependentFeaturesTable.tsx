import { FC, MouseEvent } from 'react'
import { DependencyEdge } from 'common/types/responses'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'

type DependentFeaturesTableProps = {
  edges: DependencyEdge[]
  // Opens that feature's own Dependencies tab.
  onSelect: (edge: DependencyEdge) => void
}

const DependentFeaturesTable: FC<DependentFeaturesTableProps> = ({
  edges,
  onSelect,
}) => (
  <table className='feature-dependencies__table'>
    <thead>
      <tr>
        <th scope='col'>Feature</th>
        <th
          className='feature-dependencies__actions-cell'
          aria-label='Actions'
        />
      </tr>
    </thead>
    <tbody>
      {edges.map((edge) => (
        <tr
          key={edge.feature.id}
          className='feature-dependencies__row--clickable'
          onClick={() => onSelect(edge)}
        >
          <td className='feature-dependencies__name'>
            <Button
              theme='text'
              onClick={(e: MouseEvent) => {
                e.stopPropagation()
                onSelect(edge)
              }}
            >
              {edge.feature.name}
            </Button>
          </td>
          <td className='feature-dependencies__actions-cell' aria-hidden>
            <Icon
              name='chevron-right'
              width={16}
              fill='var(--color-icon-disabled)'
            />
          </td>
        </tr>
      ))}
    </tbody>
  </table>
)

export default DependentFeaturesTable
