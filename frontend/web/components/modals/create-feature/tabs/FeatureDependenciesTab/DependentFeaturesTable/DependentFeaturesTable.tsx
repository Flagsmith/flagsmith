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
  <Table variant='ghost' layout='fixed' hover>
    <Table.Header>
      <Table.Row>
        <Table.ColumnHeader>Feature</Table.ColumnHeader>
        <Table.ColumnHeader
          className='prerequisite-actions text-end'
          aria-label='Actions'
        />
      </Table.Row>
    </Table.Header>
    <Table.Body>
      {edges.map((edge) => (
        <Table.Row
          key={edge.feature.id}
          className='cursor-pointer'
          onClick={() => onSelect(edge)}
        >
          <Table.Cell className='prerequisite-name text-truncate'>
            <Button
              theme='text'
              onClick={(e: MouseEvent) => {
                e.stopPropagation()
                onSelect(edge)
              }}
            >
              {edge.feature.name}
            </Button>
          </Table.Cell>
          <Table.Cell className='prerequisite-actions text-end' aria-hidden>
            <Icon
              name='chevron-right'
              width={16}
              fill='var(--color-icon-disabled)'
            />
          </Table.Cell>
        </Table.Row>
      ))}
    </Table.Body>
  </Table>
)

export default DependentFeaturesTable
