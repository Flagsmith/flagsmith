import { FC, ReactNode } from 'react'
import cn from 'classnames'
import { DependencyEdge } from 'common/types/responses'
import IconButton from 'components/base/IconButton'
import Icon from 'components/icons/Icon'
import Tooltip from 'components/Tooltip'
import { PrerequisiteRow } from './prerequisiteState'

// The actions column only exists where the user can manage dependencies, so a
// row spanning the table has to know that too.
export const prerequisiteColumnCount = (canManage: boolean) =>
  canManage ? 4 : 3

type PrerequisitesTableProps = {
  rows: PrerequisiteRow[]
  canManage: boolean
  highlightedId?: number
  isRemoving?: number
  onRemove: (edge: DependencyEdge) => void
  // Rendered as the last row while adding.
  addRow?: ReactNode
}

// A span, not a Switch: nothing here edits the prerequisite.
const StateToggle: FC<{ isEnabled: boolean }> = ({ isEnabled }) => (
  <span
    className={cn('feature-dependencies__toggle', {
      'feature-dependencies__toggle--on': isEnabled,
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
            className='feature-dependencies__satisfies'
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
      className={`feature-dependencies__satisfies${
        isMet ? ' feature-dependencies__satisfies--met' : ''
      }`}
    >
      <Icon name={isMet ? 'checkmark-circle' : 'minus-circle'} width={16} />
      {isMet ? 'Yes' : 'No'}
    </span>
  )
}

const PrerequisitesTable: FC<PrerequisitesTableProps> = ({
  addRow,
  canManage,
  highlightedId,
  isRemoving,
  onRemove,
  rows,
}) => (
  <table className='feature-dependencies__table'>
    <thead>
      <tr>
        <th scope='col'>Prerequisite</th>
        <th scope='col'>Status</th>
        <th scope='col'>Satisfies</th>
        {canManage && (
          <th
            className='feature-dependencies__actions-cell text-end'
            aria-label='Actions'
          />
        )}
      </tr>
    </thead>
    <tbody>
      {rows.map(({ edge, isEnabled, isMet }) => (
        <tr
          key={edge.prerequisite.id}
          className={cn({
            'feature-dependencies__row--added':
              highlightedId === edge.prerequisite.id,
            // Dimmed while the DELETE is in flight.
            'feature-dependencies__row--removing':
              isRemoving === edge.prerequisite.id,
          })}
        >
          <td className='feature-dependencies__name text-truncate'>
            {edge.prerequisite.name}
          </td>
          <td>
            <StateToggle isEnabled={isEnabled} />
          </td>
          <td>
            <Satisfies isMet={isMet} />
          </td>
          {canManage && (
            <td className='feature-dependencies__actions-cell text-end'>
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
      {addRow}
    </tbody>
  </table>
)

export default PrerequisitesTable
