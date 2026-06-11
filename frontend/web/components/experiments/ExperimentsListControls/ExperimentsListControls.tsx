import { ChangeEvent, FC } from 'react'
import Utils from 'common/utils/utils'
import SearchInput from 'components/base/forms/SearchInput'
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
        <SearchInput
          value={searchInput}
          onChange={(e: ChangeEvent<HTMLInputElement>) =>
            onSearchChange(Utils.safeParseEventValue(e))
          }
          placeholder='Search experiments...'
          size='small'
        />
      </div>
    </div>
  )
}

export default ExperimentsListControls
