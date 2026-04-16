import React, { FC, useMemo, useState } from 'react'
import { useHistory } from 'react-router-dom'
import Button from 'components/base/forms/Button'
import Input from 'components/base/forms/Input'
import EmptyState from 'components/EmptyState'
import StatusBadge from './shared/StatusBadge'
import { ExperimentListItem, ExperimentStatus, MOCK_EXPERIMENTS } from './types'
import './ExperimentsListPage.scss'

type FilterTab = 'all' | ExperimentStatus

const TABS: { label: string; value: FilterTab }[] = [
  { label: 'All', value: 'all' },
  { label: 'Running', value: 'running' },
  { label: 'Draft', value: 'draft' },
  { label: 'Completed', value: 'completed' },
]

const ExperimentsListPage: FC = () => {
  const history = useHistory()
  const [activeTab, setActiveTab] = useState<FilterTab>('all')
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    let items = MOCK_EXPERIMENTS
    if (activeTab !== 'all') {
      items = items.filter((e) => e.status === activeTab)
    }
    if (search) {
      const lower = search.toLowerCase()
      items = items.filter(
        (e) =>
          e.name.toLowerCase().includes(lower) ||
          e.linkedFlag.toLowerCase().includes(lower),
      )
    }
    return items
  }, [activeTab, search])

  const counts = useMemo(() => {
    const c = { completed: 0, draft: 0, paused: 0, running: 0 }
    MOCK_EXPERIMENTS.forEach((e) => {
      c[e.status]++
    })
    return c
  }, [])

  const handleRowClick = (experiment: ExperimentListItem) => {
    // Navigate to results page (mock: uses current route context)
    history.push(
      `${document.location.pathname.replace('/experiments', '')}/experiments/${
        experiment.id
      }`,
    )
  }

  return (
    <div className='experiments-list-page'>
      <div className='experiments-list-page__header'>
        <h3>Experiments</h3>
        <Button
          theme='primary'
          size='default'
          iconLeft='plus'
          onClick={() =>
            history.push(
              `${document.location.pathname.replace(
                '/experiments',
                '',
              )}/experiments/create`,
            )
          }
        >
          Create Experiment
        </Button>
      </div>

      <div className='experiments-list-page__controls'>
        <div className='experiments-list-page__tabs'>
          {TABS.map((tab) => (
            <button
              key={tab.value}
              type='button'
              className={`experiments-list-page__tab ${
                activeTab === tab.value
                  ? 'experiments-list-page__tab--active'
                  : ''
              }`}
              onClick={() => setActiveTab(tab.value)}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <div className='experiments-list-page__search'>
          <Input
            value={search}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setSearch(e.target.value)
            }
            placeholder='Search experiments...'
            search
            size='small'
          />
        </div>
      </div>

      {filtered.length > 0 ? (
        <>
          <table className='experiments-list-page__table'>
            <thead>
              <tr>
                <th>Experiment Name</th>
                <th>Linked Flag</th>
                <th>Status</th>
                <th>Variations</th>
                <th>Primary Metric</th>
                <th>Last Updated</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((exp) => (
                <tr
                  key={exp.id}
                  className='experiments-list-page__row'
                  onClick={() => handleRowClick(exp)}
                >
                  <td className='fw-medium'>{exp.name}</td>
                  <td>
                    <code className='experiments-list-page__flag-name'>
                      {exp.linkedFlag}
                    </code>
                  </td>
                  <td>
                    <StatusBadge status={exp.status} />
                  </td>
                  <td>{exp.variations}</td>
                  <td>{exp.primaryMetric}</td>
                  <td className='text-secondary'>{exp.lastUpdated}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className='experiments-list-page__footer'>
            {MOCK_EXPERIMENTS.length} experiments &middot; {counts.running}{' '}
            running &middot; {counts.draft} draft &middot; {counts.completed}{' '}
            completed
          </div>
        </>
      ) : (
        <EmptyState
          title='No experiments'
          description={
            search
              ? `No experiments found for "${search}"`
              : 'Create your first experiment to start testing.'
          }
          icon='bar-chart'
          action={
            !search ? (
              <Button
                theme='primary'
                size='small'
                onClick={() =>
                  history.push(
                    `${document.location.pathname.replace(
                      '/experiments',
                      '',
                    )}/experiments/create`,
                  )
                }
              >
                Create Experiment
              </Button>
            ) : undefined
          }
        />
      )}
    </div>
  )
}

export default ExperimentsListPage
