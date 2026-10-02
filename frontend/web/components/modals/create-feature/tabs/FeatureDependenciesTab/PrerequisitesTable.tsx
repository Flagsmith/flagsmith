import { FC, ReactNode } from 'react'
import cn from 'classnames'
import { DependencyEdge } from 'common/types/responses'
import IconButton from 'components/base/IconButton'
import Icon from 'components/icons/Icon'
import Tooltip from 'components/Tooltip'

export type PrerequisiteRow = {
  edge: DependencyEdge
  // The prerequisite's own state in this environment. One with no feature state
  // resolved yet is treated as off.
  isEnabled: boolean
  // Whether that state satisfies the rule. Only known for a system edge, where
  // the rule is always "must be enabled". Undefined otherwise.
  isMet?: boolean
}

type PrerequisitesTableProps = {
  rows: PrerequisiteRow[]
  canManage: boolean
  // The row just added, highlighted briefly so it can be picked out of a list
  // that is not ordered by recency.
  highlightedId?: number
  isRemoving?: number
  onRemove: (edge: DependencyEdge) => void
  // The picker, rendered as the last row while adding. Selecting commits it,
  // so the draft row never outlives the interaction.
  addRow?: ReactNode
}

// Borrows the toggle's silhouette without being a control: a span, not a
// button, at full contrast rather than rc-switch's disabled grey. Nothing here
// edits the prerequisite, so nothing should invite a click.
const StateToggle: FC<{ isEnabled: boolean }> = ({ isEnabled }) => (
  <span
    className={`feature-dependencies__toggle${
      isEnabled ? ' feature-dependencies__toggle--on' : ''
    }`}
    role='img'
    aria-label={isEnabled ? 'On' : 'Off'}
  />
)

// Two columns on two different axes: Status is the prerequisite's own state,
// Satisfies is whether that state meets this flag's rule. They agree on every
// row today, and stop agreeing as soon as a rule can be something other than
// "must be enabled". Only Satisfies carries colour.
const Satisfies: FC<{ isMet?: boolean }> = ({ isMet }) => {
  if (isMet === undefined) {
    return (
      <Tooltip
        title={
          <span className='feature-dependencies__satisfies'>
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
            className='feature-dependencies__actions-cell'
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
            // The row stays put while the DELETE is in flight, dimmed, so the
            // gap between confirming and the refetch is not silent.
            'feature-dependencies__row--removing':
              isRemoving === edge.prerequisite.id,
          })}
        >
          <td className='feature-dependencies__name'>
            {edge.prerequisite.name}
          </td>
          <td>
            <StateToggle isEnabled={isEnabled} />
          </td>
          <td>
            <Satisfies isMet={isMet} />
          </td>
          {canManage && (
            <td className='feature-dependencies__actions-cell'>
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
