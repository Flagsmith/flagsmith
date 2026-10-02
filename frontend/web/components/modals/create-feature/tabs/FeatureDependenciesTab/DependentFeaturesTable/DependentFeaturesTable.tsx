import { FC, MouseEvent } from 'react'
import { DependencyEdge } from 'common/types/responses'
import Button from 'components/base/forms/Button'
import Table from 'components/base/Table'
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
  <Table variant='ghost' layout='fixed'>
    <Table.Header>
      <Table.Row>
        <Table.ColumnHeader>Feature</Table.ColumnHeader>
        <th className='prerequisite-actions text-end' aria-label='Actions' />
      </Table.Row>
    </Table.Header>
    <Table.Body>
      {edges.map((edge) => (
        <tr
          key={edge.feature.id}
          className='cursor-pointer'
          onClick={() => onSelect(edge)}
        >
          <td className='prerequisite-name text-truncate'>
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
          <td className='prerequisite-actions text-end' aria-hidden>
            <Icon
              name='chevron-right'
              width={16}
              fill='var(--color-icon-disabled)'
            />
          </td>
        </tr>
      ))}
    </Table.Body>
  </Table>
)

export default DependentFeaturesTable
