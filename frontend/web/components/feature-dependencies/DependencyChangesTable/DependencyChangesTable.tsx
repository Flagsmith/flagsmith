import { FC } from 'react'
import { StagedDependencyChange } from 'common/types/responses'
import Chip from 'components/base/Chip'
import './DependencyChangesTable.scss'
import Table, {
  TableBody,
  TableCell,
  TableColumnHeader,
  TableHeader,
  TableRow,
} from 'components/base/Table'

type DependencyChangesTableProps = {
  changes: StagedDependencyChange[]
}

// What a change request does to a feature's prerequisites once published.
const DependencyChangesTable: FC<DependencyChangesTableProps> = ({
  changes,
}) => (
  <Table variant='ghost' layout='fixed'>
    <TableHeader>
      <TableRow>
        <TableColumnHeader className='dependency-changes__change'>
          Change
        </TableColumnHeader>
        <TableColumnHeader>Prerequisite</TableColumnHeader>
      </TableRow>
    </TableHeader>
    <TableBody>
      {changes.map(({ action, prerequisite }) => (
        <TableRow key={prerequisite.id}>
          <TableCell>
            <Chip size='xs' variant={action === 'add' ? 'accent' : 'neutral'}>
              {action === 'add' ? 'Add' : 'Remove'}
            </Chip>
          </TableCell>
          <TableCell className='font-weight-medium text-truncate'>
            {prerequisite.name}
          </TableCell>
        </TableRow>
      ))}
    </TableBody>
  </Table>
)

export default DependencyChangesTable
