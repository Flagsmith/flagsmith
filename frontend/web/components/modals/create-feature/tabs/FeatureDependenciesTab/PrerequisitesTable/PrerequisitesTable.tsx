import { FC, ReactNode } from 'react'
import cn from 'classnames'
import { DependencyEdge } from 'common/types/responses'
import Button from 'components/base/forms/Button'
import Table from 'components/base/Table'
import IconButton from 'components/base/IconButton'
import Icon from 'components/icons/Icon'
import Tooltip from 'components/Tooltip'
import { PrerequisiteRow } from 'components/modals/create-feature/tabs/FeatureDependenciesTab/prerequisiteState'
import './PrerequisitesTable.scss'

// The actions column only exists where the user can manage dependencies, so the
// picker row has to span a different number of columns.
const columnCount = (canManage: boolean) => (canManage ? 4 : 3)

type PrerequisitesTableProps = {
  rows: PrerequisiteRow[]
  canManage: boolean
  highlightedId?: number
  isRemoving?: number
  onRemove: (edge: DependencyEdge) => void
  // The picker, shown as the last row. Selecting commits it, so the draft row
  // never outlives the interaction.
  addControl?: ReactNode
  onCancelAdd?: () => void
}

// A span, not a Switch: nothing here edits the prerequisite.
const StateToggle: FC<{ isEnabled: boolean }> = ({ isEnabled }) => (
  <span
    className={cn('prerequisite-toggle', {
      'prerequisite-toggle--on': isEnabled,
    })}
    role='img'
    aria-label={isEnabled ? 'On' : 'Off'}
  />
)

// Status is the prerequisite's own state; Satisfies is whether that state meets
// this flag's rule. Only Satisfies carries colour.
const Satisfies: FC<{ isMet?: boolean }> = ({ isMet }) => {
  if (isMet === undefined) {
    return (
      <Tooltip
        title={
          <span
            className='d-inline-flex align-items-center gap-1 text-secondary'
            role='img'
            aria-label='Unknown'
          >
            <Icon name='info-outlined' width={16} />
          </span>
        }
        place='top'
      >
        This comes from a segment you wrote, so Flagsmith cannot tell which
        state it expects.
      </Tooltip>
    )
  }
  // Only the satisfied rows are coloured; the banner carries the warning.
  return (
    <span
      className={cn(
        'd-inline-flex align-items-center gap-1',
        isMet ? 'text-success' : 'text-secondary',
      )}
    >
      <Icon name={isMet ? 'checkmark-circle' : 'minus-circle'} width={16} />
      {isMet ? 'Yes' : 'No'}
    </span>
  )
}

const PrerequisitesTable: FC<PrerequisitesTableProps> = ({
  addControl,
  canManage,
  highlightedId,
  isRemoving,
  onCancelAdd,
  onRemove,
  rows,
}) => (
  <Table variant='ghost' layout='fixed'>
    <Table.Header>
      <Table.Row>
        <Table.ColumnHeader>Prerequisite</Table.ColumnHeader>
        <Table.ColumnHeader>Status</Table.ColumnHeader>
        <Table.ColumnHeader>Satisfies</Table.ColumnHeader>
        {canManage && (
          <th className='prerequisite-actions text-end' aria-label='Actions' />
        )}
      </Table.Row>
    </Table.Header>
    <Table.Body>
      {rows.map(({ edge, isEnabled, isMet }) => (
        <tr
          key={edge.prerequisite.id}
          className={cn({
            'prerequisite-row--added': highlightedId === edge.prerequisite.id,
            // Dimmed while the DELETE is in flight.
            'prerequisite-row--removing': isRemoving === edge.prerequisite.id,
          })}
        >
          <td className='prerequisite-name text-truncate'>
            {edge.prerequisite.name}
          </td>
          <td>
            <StateToggle isEnabled={isEnabled} />
          </td>
          <td>
            <Satisfies isMet={isMet} />
          </td>
          {canManage && (
            <td className='prerequisite-actions text-end'>
              {/* An edge from a hand-written segment condition cannot be removed
                through the dependencies API, so it gets no control. */}
              {edge.segment.is_system && (
                <IconButton
                  size='medium'
                  variant='ghost'
                  disabled={isRemoving === edge.prerequisite.id}
                  onClick={() => onRemove(edge)}
                  aria-label={`Remove ${edge.prerequisite.name} as a prerequisite`}
                >
                  <Icon name='trash-2' width={20} />
                </IconButton>
              )}
            </td>
          )}
        </tr>
      ))}
      {!!addControl && (
        <tr className='prerequisite-add-row'>
          {/* One cell: the picker has no column to line up with. */}
          <td colSpan={columnCount(canManage)}>
            <div className='prerequisite-add-control d-flex align-items-center gap-2'>
              {addControl}
              <Button theme='text' onClick={onCancelAdd}>
                Cancel
              </Button>
            </div>
          </td>
        </tr>
      )}
    </Table.Body>
  </Table>
)

export default PrerequisitesTable
