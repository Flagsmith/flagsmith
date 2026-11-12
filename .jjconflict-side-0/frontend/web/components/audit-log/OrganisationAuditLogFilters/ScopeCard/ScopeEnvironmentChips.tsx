import { FC, KeyboardEvent } from 'react'
import ToggleChip from 'components/base/ToggleChip'
import ListMessage, { ScopeList } from './ListMessage'
import { getArrowTarget } from './arrowTarget'

// Arrows move focus between the chips; Tab and Space still work as usual.
const moveFocus = (e: KeyboardEvent<HTMLDivElement>) => {
  const inputs = [...e.currentTarget.querySelectorAll('input')]
  const index = inputs.findIndex((input) => input === document.activeElement)
  const target =
    index === -1 ? null : getArrowTarget(e.key, index, inputs.length)
  if (target === null) return
  e.preventDefault()
  inputs[target].focus()
}

export type ScopeCardEnvironment = { id: number; name: string; colour: string }

type ScopeEnvironmentChipsProps = {
  environments: ScopeList<ScopeCardEnvironment>
  selectedIds: number[]
  onToggle: (environmentId: number, checked: boolean) => void
}

const ScopeEnvironmentChips: FC<ScopeEnvironmentChipsProps> = ({
  environments,
  onToggle,
  selectedIds,
}) => (
  <div
    role='group'
    aria-label='Environments'
    // p-1: room for the focus ring, which the section would clip.
    className='d-flex flex-wrap gap-2 p-1'
    onKeyDown={moveFocus}
  >
    <ListMessage
      list={environments}
      noun='environments'
      emptyText='This project has no environments'
    />
    {environments.items.map((environment) => (
      <ToggleChip
        key={environment.id}
        checked={selectedIds.includes(environment.id)}
        colour={environment.colour}
        onChange={(checked) => onToggle(environment.id, checked)}
      >
        {environment.name}
      </ToggleChip>
    ))}
  </div>
)

export default ScopeEnvironmentChips
