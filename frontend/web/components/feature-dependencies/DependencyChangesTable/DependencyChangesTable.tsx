import { FC } from 'react'
import { StagedDependencyChange } from 'common/types/responses'
import cn from 'classnames'
import StateToggle from 'components/modals/create-feature/tabs/FeatureDependenciesTab/StateToggle'
import Satisfies from 'components/modals/create-feature/tabs/FeatureDependenciesTab/Satisfies'
import 'components/diff/DiffRow/DiffRow.scss'
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
  // Adds the live table's Status and Satisfies columns for this environment.
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
        <TableColumnHeader
          className='dependency-changes__change'
          aria-label='Change'
        />
        <TableColumnHeader>Prerequisite</TableColumnHeader>
        {!!isEnabled && (
          <>
            <TableColumnHeader className='dependency-changes__state'>
              Status
            </TableColumnHeader>
            <TableColumnHeader className='dependency-changes__state'>
              Satisfies
            </TableColumnHeader>
          </>
        )}
      </TableRow>
    </TableHeader>
    <TableBody>
      {changes.map(({ action, prerequisite }) => {
        const isAdd = action === 'add'
        return (
          // The change request diff's rows, so a change reads the same here.
          <TableRow
            key={prerequisite.id}
            className={cn(
              'diff-row',
              isAdd ? 'diff-row--added' : 'diff-row--removed',
            )}
          >
            <TableCell className='diff-row__marker p-0 text-center'>
              <pre role='img' aria-label={isAdd ? 'Add' : 'Remove'}>
                {isAdd ? '+' : '-'}
              </pre>
            </TableCell>
            <TableCell className='diff-row__content font-weight-medium text-truncate'>
              {prerequisite.name}
            </TableCell>
            {!!isEnabled && (
              <>
                <TableCell className='diff-row__content'>
                  <StateToggle isEnabled={isEnabled(prerequisite.id)} />
                </TableCell>
                <TableCell className='diff-row__content'>
                  {/* Only system edges can be staged, so on means met. */}
                  <Satisfies isMet={isEnabled(prerequisite.id)} />
                </TableCell>
              </>
            )}
          </TableRow>
        )
      })}
    </TableBody>
  </Table>
)

export default DependencyChangesTable
