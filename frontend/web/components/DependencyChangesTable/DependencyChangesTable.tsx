import { FC } from 'react'
import { StagedDependencyChange } from 'common/types/responses'
import { colorTextAction, colorTextDanger } from 'common/theme/tokens'
import Chip from 'components/base/Chip'
import Icon from 'components/icons/Icon'
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
  // Adds a column with each prerequisite's state in this environment.
  isEnabled?: (prerequisiteId: number) => boolean
}

// What a change request does to a feature's prerequisites once published.
const DependencyChangesTable: FC<DependencyChangesTableProps> = ({
  changes,
  isEnabled,
}) => (
  <Table variant='ghost' layout='fixed'>
    <TableHeader>
      <TableRow>
        <TableColumnHeader className='dependency-changes__change'>
          Change
        </TableColumnHeader>
        <TableColumnHeader>Prerequisite</TableColumnHeader>
        {!!isEnabled && (
          <TableColumnHeader className='dependency-changes__state text-end'>
            Current state
          </TableColumnHeader>
        )}
      </TableRow>
    </TableHeader>
    <TableBody>
      {changes.map(({ action, prerequisite }) => {
        const isAdd = action === 'add'
        return (
          <TableRow key={prerequisite.id}>
            <TableCell>
              <span className='d-inline-flex align-items-center gap-2'>
                <Icon
                  name={isAdd ? 'plus' : 'minus'}
                  width={16}
                  fill={isAdd ? colorTextAction : colorTextDanger}
                  aria-hidden
                />
                <Chip size='xs' variant={isAdd ? 'accent' : 'danger'}>
                  {isAdd ? 'Add' : 'Remove'}
                </Chip>
              </span>
            </TableCell>
            <TableCell className='font-weight-medium text-truncate'>
              {prerequisite.name}
            </TableCell>
            {!!isEnabled && (
              <TableCell className='text-end'>
                <Chip size='xs'>
                  {isEnabled(prerequisite.id) ? 'Enabled' : 'Disabled'}
                </Chip>
              </TableCell>
            )}
          </TableRow>
        )
      })}
    </TableBody>
  </Table>
)

export default DependencyChangesTable
