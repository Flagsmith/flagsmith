import { FC, MouseEvent } from 'react'
import { DependencyEdge } from 'common/types/responses'
import Button from 'components/base/forms/Button'
import Table, {
  TableBody,
  TableCell,
  TableColumnHeader,
  TableHeader,
  TableRow,
} from 'components/base/Table'
import Icon from 'components/icons/Icon'

type DependentFeaturesTableProps = {
  edges: DependencyEdge[]
  onSelect: (edge: DependencyEdge) => void
}

const DependentFeaturesTable: FC<DependentFeaturesTableProps> = ({
  edges,
  onSelect,
}) => (
  <Table variant='ghost' layout='fixed' hover>
    <TableHeader>
      <TableRow>
        <TableColumnHeader>Feature</TableColumnHeader>
        <TableColumnHeader
          className='ds-table__actions text-end'
          aria-label='Actions'
        />
      </TableRow>
    </TableHeader>
    <TableBody>
      {edges.map((edge) => (
        <TableRow
          key={edge.feature.id}
          className='cursor-pointer'
          onClick={() => onSelect(edge)}
        >
          <TableCell className='font-weight-medium text-truncate'>
            <Button
              theme='text'
              onClick={(e: MouseEvent) => {
                e.stopPropagation()
                onSelect(edge)
              }}
            >
              {edge.feature.name}
            </Button>
          </TableCell>
          <TableCell className='ds-table__actions text-end' aria-hidden>
            <Icon
              name='chevron-right'
              width={16}
              fill='var(--color-icon-disabled)'
            />
          </TableCell>
        </TableRow>
      ))}
    </TableBody>
  </Table>
)

export default DependentFeaturesTable
