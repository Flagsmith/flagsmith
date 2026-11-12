import { FC } from 'react'
import ToggleChip from 'components/base/ToggleChip'
import ListMessage, { ScopeList } from './ListMessage'

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
    className='d-flex flex-wrap gap-2 px-1 pb-1'
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
