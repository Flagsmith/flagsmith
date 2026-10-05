import { FC, MouseEvent, ReactNode } from 'react'
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
  onSelect: (edge: DependencyEdge) => void
  addControl?: ReactNode
  onCancelAdd?: () => void
}

const StateToggle: FC<{ isEnabled: boolean }> = ({ isEnabled }) => (
  <Icon
    name={isEnabled ? 'toggle-on' : 'toggle-off'}
    width={32}
    fill={
      isEnabled
        ? 'var(--color-surface-action)'
        : 'var(--color-surface-emphasis)'
    }
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
  canManage,
  highlightedId,
  isRemoving,
  onCancelAdd,
  onRemove,
  onSelect,
  rows,
}) => (
  <Table variant='ghost' layout='fixed' hover>
    <Table.Header>
      <Table.Row>
        <Table.ColumnHeader>Prerequisite</Table.ColumnHeader>
        <Table.ColumnHeader>Status</Table.ColumnHeader>
        <Table.ColumnHeader>Satisfies</Table.ColumnHeader>
        {canManage && (
          <Table.ColumnHeader
            className='ds-table__actions text-end'
            aria-label='Actions'
          />
        )}
      </Table.Row>
    </Table.Header>
    <Table.Body>
      {rows.map(({ edge, isEnabled, isMet }) => (
        <Table.Row
          key={edge.prerequisite.id}
          state={
            (highlightedId === edge.prerequisite.id && 'added') ||
            (isRemoving === edge.prerequisite.id && 'pending') ||
            undefined
          }
        >
          <Table.Cell className='prerequisite-name text-truncate'>
            <Button
              theme='text'
              onClick={(e: MouseEvent) => {
                e.stopPropagation()
                onSelect(edge)
              }}
            >
              {edge.prerequisite.name}
            </Button>
          </Table.Cell>
          <Table.Cell>
            <StateToggle isEnabled={isEnabled} />
          </Table.Cell>
          <Table.Cell>
            <Satisfies isMet={isMet} />
          </Table.Cell>
          {canManage && (
            <Table.Cell className='ds-table__actions text-end'>
              {/* An edge from a hand-written segment condition cannot be removed
                through the dependencies API, so it gets no control. */}
              {edge.segment.is_system && (
                <IconButton
                  size='small'
                  variant='ghost'
                  disabled={isRemoving === edge.prerequisite.id}
                  onClick={() => onRemove(edge)}
                  aria-label={`Remove ${edge.prerequisite.name} as a prerequisite`}
                >
                  <Icon name='trash-2' width={16} />
                </IconButton>
              )}
            </Table.Cell>
          )}
        </Table.Row>
      ))}
      {!!addControl && (
        <Table.Row state='editor'>
          {/* One cell: the picker has no column to line up with. */}
          <Table.Cell colSpan={columnCount(canManage)}>
            <div className='prerequisite-add-control d-flex align-items-center gap-2'>
              {addControl}
              <Button theme='text' onClick={onCancelAdd}>
                Cancel
              </Button>
            </div>
          </Table.Cell>
        </Table.Row>
      )}
    </Table.Body>
  </Table>
)

export default PrerequisitesTable
