import { FC } from 'react'
import { FlagBisectIncident } from 'common/types/responses'
import { stateLabel, stateTone } from './utils'

const StateBadge: FC<{ state: FlagBisectIncident['state'] }> = ({ state }) => (
  <span
    className={`flag-bisect__badge flag-bisect__badge--${stateTone(state)}`}
  >
    {stateLabel(state)}
  </span>
)

export default StateBadge
