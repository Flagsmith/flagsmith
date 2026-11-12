import { FC } from 'react'
import Chip from 'components/base/Chip'
import ColorSwatch from 'components/ColorSwatch'
import { getEnvironmentColour } from 'common/utils/paletteColour'
import ListMessage, { ScopeList } from './ListMessage'

export type ScopeCardEnvironment = { id: number; name: string }

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
      <Chip
        key={environment.id}
        checked={selectedIds.includes(environment.id)}
        onChange={(checked) => onToggle(environment.id, checked)}
      >
        <ColorSwatch
          color={getEnvironmentColour(environment.id)}
          shape='circle'
          size='sm'
        />
        {environment.name}
      </Chip>
    ))}
  </div>
)

export default ScopeEnvironmentChips
