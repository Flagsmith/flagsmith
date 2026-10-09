import { FC, MouseEvent, ReactNode } from 'react'
import cn from 'classnames'
import { DependencyEdge } from 'common/types/responses'
import { colorSurfaceAction, colorSurfaceEmphasis } from 'common/theme/tokens'
import Button from 'components/base/forms/Button'
import Chip from 'components/base/Chip'
import Table, {
  TableBody,
  TableCell,
  TableColumnHeader,
  TableHeader,
  TableRow,
} from 'components/base/Table'
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
  flashedId?: number
  isRemoving?: number
  onRemove: (edge: DependencyEdge) => void
  // Takes back a held removal.
  onUndo?: (edge: DependencyEdge) => void
  // The row a change request refused, marked until the user acts.
  refusedId?: number
  onSelect: (edge: DependencyEdge) => void
  // The prerequisite being added, shown as a row of its own until the POST
  // resolves. Otherwise nothing moves between picking one and it appearing.
  addingName?: string
  addControl?: ReactNode
  onCancelAdd?: () => void
}

const StateToggle: FC<{ isEnabled: boolean }> = ({ isEnabled }) => (
  <Icon
    name={isEnabled ? 'toggle-on' : 'toggle-off'}
    width={32}
    fill={isEnabled ? colorSurfaceAction : colorSurfaceEmphasis}
    role='img'
    aria-label={isEnabled ? 'On' : 'Off'}
  />
)

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
  addingName,
  canManage,
  flashedId,
  isRemoving,
  onCancelAdd,
  onRemove,
  onSelect,
  onUndo,
  refusedId,
  rows,
}) => (
  <Table variant='ghost' layout='fixed' highlightRowOnHover>
    <TableHeader>
      <TableRow>
        <TableColumnHeader>Prerequisite</TableColumnHeader>
        <TableColumnHeader>Status</TableColumnHeader>
        <TableColumnHeader>Satisfies</TableColumnHeader>
        {canManage && (
          <TableColumnHeader
            className='ds-table__actions text-end'
            aria-label='Actions'
          />
        )}
      </TableRow>
    </TableHeader>
    <TableBody>
      {rows.map(({ edge, isEnabled, isMet, staged }) => (
        <TableRow
          key={edge.prerequisite.id}
          className={cn('cursor-pointer', {
            'prerequisite-row--flash': flashedId === edge.prerequisite.id,
            'prerequisite-row--refused': refusedId === edge.prerequisite.id,
            'prerequisite-row--staged-remove': staged === 'remove',
          })}
          onClick={() => onSelect(edge)}
          pending={isRemoving === edge.prerequisite.id}
        >
          <TableCell className='font-weight-medium'>
            {/* The name gives way to the chip, so a long name cannot hide
                what is about to happen to it. */}
            <div className='prerequisite-name d-flex align-items-center gap-2'>
              <Button
                theme='text'
                className='justify-content-start'
                onClick={(e: MouseEvent) => {
                  e.stopPropagation()
                  onSelect(edge)
                }}
              >
                <span className='prerequisite-name__text text-truncate'>
                  {edge.prerequisite.name}
                </span>
              </Button>
              {!!staged && (
                <Chip
                  size='xs'
                  variant={staged === 'add' ? 'accent' : 'neutral'}
                  className='flex-shrink-0'
                >
                  {staged === 'add' ? 'Staged: add' : 'Staged: remove'}
                </Chip>
              )}
            </div>
          </TableCell>
          <TableCell>
            <StateToggle isEnabled={isEnabled} />
          </TableCell>
          <TableCell>
            <Satisfies isMet={isMet} />
          </TableCell>
          {canManage && (
            <TableCell className='ds-table__actions text-end'>
              {staged === 'remove' && onUndo ? (
                <IconButton
                  size='small'
                  variant='ghost'
                  onClick={(e: MouseEvent) => {
                    e.stopPropagation()
                    onUndo(edge)
                  }}
                  aria-label={`Keep ${edge.prerequisite.name} as a prerequisite`}
                >
                  <Icon name='refresh' width={16} />
                </IconButton>
              ) : (
                // An edge from a hand-written segment condition cannot be
                // removed through the dependencies API, so it gets no control.
                edge.segment.is_system && (
                  <IconButton
                    size='small'
                    variant='ghost'
                    disabled={isRemoving === edge.prerequisite.id}
                    onClick={(e: MouseEvent) => {
                      e.stopPropagation()
                      onRemove(edge)
                    }}
                    aria-label={`Remove ${edge.prerequisite.name} as a prerequisite`}
                  >
                    <Icon name='trash-2' width={16} />
                  </IconButton>
                )
              )}
            </TableCell>
          )}
        </TableRow>
      ))}
      {/* Dropped the moment the real row lands, or the flag is listed twice. */}
      {!!addingName &&
        !rows.some((row) => row.edge.prerequisite.name === addingName) && (
          <TableRow pending>
            <TableCell className='font-weight-medium text-truncate'>
              {addingName}
            </TableCell>
            <TableCell colSpan={columnCount(canManage) - 1} />
          </TableRow>
        )}
      {!!addControl && (
        <TableRow className='prerequisite-row--input'>
          {/* One cell: the picker has no column to line up with. */}
          <TableCell colSpan={columnCount(canManage)}>
            <div className='prerequisite-add-control d-flex align-items-center gap-2'>
              {addControl}
              <Button theme='text' onClick={onCancelAdd}>
                Cancel
              </Button>
            </div>
          </TableCell>
        </TableRow>
      )}
    </TableBody>
  </Table>
)

export default PrerequisitesTable
