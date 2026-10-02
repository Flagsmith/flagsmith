import { FC, MouseEvent } from 'react'
import { DependencyEdge } from 'common/types/responses'
import Button from 'components/base/forms/Button'
import DependenciesTable from 'components/modals/create-feature/tabs/FeatureDependenciesTab/DependenciesTable'
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
  <DependenciesTable
    head={
      <>
        <th scope='col'>Feature</th>
        <th
          className='dependencies-table__actions text-end'
          aria-label='Actions'
        />
      </>
    }
  >
    {edges.map((edge) => (
      <tr
        key={edge.feature.id}
        className='cursor-pointer'
        onClick={() => onSelect(edge)}
      >
        <td className='dependencies-table__name text-truncate'>
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
        <td className='dependencies-table__actions text-end' aria-hidden>
          <Icon
            name='chevron-right'
            width={16}
            fill='var(--color-icon-disabled)'
          />
        </td>
      </tr>
    ))}
  </DependenciesTable>
)

export default DependentFeaturesTable
