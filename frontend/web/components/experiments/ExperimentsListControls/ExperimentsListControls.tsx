import { FC } from 'react'
import { FilterTab } from 'components/experiments/constants'
import './ExperimentsListControls.scss'

type ExperimentsListControlsProps = {
  tabs: { value: FilterTab; label: string }[]
  activeTab: FilterTab
  onTabChange: (tab: FilterTab) => void
  searchInput: string
  onSearchChange: (value: string) => void
}

const ExperimentsListControls: FC<ExperimentsListControlsProps> = ({
  activeTab,
  onSearchChange,
  onTabChange,
  searchInput,
  tabs,
}) => {
  return (
    <div className='experiments-controls'>
      <div className='experiments-controls__tabs'>
        {tabs.map((tab) => (
          <button
            key={tab.value}
            type='button'
            className={`experiments-controls__tab ${
              activeTab === tab.value ? 'experiments-controls__tab--active' : ''
            }`}
            onClick={() => onTabChange(tab.value)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className='experiments-controls__search'>
        <Input
          value={searchInput}
          onChange={(e: InputEvent) =>
            onSearchChange(Utils.safeParseEventValue(e))
          }
          placeholder='Search experiments...'
          search
          size='small'
        />
      </div>
    </div>
  )
}

export default ExperimentsListControls
