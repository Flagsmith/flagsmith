import type { Meta, StoryObj } from 'storybook'

import Icon from 'components/icons/Icon'
import './DependencyLayouts.scss'

// Explorations only. Neither of these ships as-is; they exist so the shape of
// the data can be judged against the table the tab uses today.

type Flag = { name: string; on: boolean }

const PREREQUISITES: Flag[] = [
  { name: 'billing_engine_v2', on: true },
  { name: 'dark_mode', on: true },
  { name: 'payment_provider', on: false },
]

const MANY: Flag[] = [
  ...PREREQUISITES,
  { name: 'test_feat_with_value', on: false },
  { name: 'config_feat_test', on: false },
  { name: 'new_feat', on: false },
]

const DEPENDENTS = ['checkout_express_lane', 'one_click_pay', 'beta_programme']

const FEATURE = 'marketplace'

/* ---------------------------------------------------------------- A ---- */

const Checklist = ({ rows }: { rows: Flag[] }) => {
  const off = rows.filter((row) => !row.on).length
  return (
    <div className='explore'>
      <h5 className='mb-1'>Flag Dependencies</h5>
      <p className='text-muted mb-3'>
        {FEATURE} runs when all of these are on.
      </p>

      <ul className='explore-check'>
        {rows.map((row) => (
          <li
            key={row.name}
            className={`explore-check__row${
              row.on ? '' : ' explore-check__row--off'
            }`}
          >
            <Icon
              name={row.on ? 'checkmark-circle' : 'minus-circle'}
              width={18}
              fill={
                row.on
                  ? 'var(--color-icon-success)'
                  : 'var(--color-icon-warning)'
              }
            />
            <span className='explore-check__name'>{row.name}</span>
            {!row.on && <span className='explore-check__state'>off</span>}
            <button type='button' className='explore-check__remove'>
              <Icon name='trash-2' width={18} />
            </button>
          </li>
        ))}
      </ul>

      {!!off && (
        <p className='explore-foot'>
          {off === 1 ? '1 is off' : `${off} are off`}, so {FEATURE} is off by
          default in Development.
        </p>
      )}

      <h5 className='mt-4 mb-1'>Dependent features</h5>
      <p className='text-muted mb-0'>
        {/* Not a list to act on. One fact, stated once. */}
        {DEPENDENTS.length} flags go dark if you turn {FEATURE} off:{' '}
        {DEPENDENTS.map((name, i) => (
          <span key={name}>
            {i > 0 && ', '}
            <a href='#top' onClick={(e) => e.preventDefault()}>
              {name}
            </a>
          </span>
        ))}
        .
      </p>
    </div>
  )
}

/* ---------------------------------------------------------------- C ---- */

const Node = ({ rows }: { rows: Flag[] }) => (
  <div className='explore'>
    <h5 className='mb-3'>Flag Dependencies</h5>

    <div className='explore-graph'>
      <div className='explore-graph__tier'>
        {rows.map((row) => (
          <div
            key={row.name}
            className={`explore-node explore-node--prereq${
              row.on ? '' : ' explore-node--off'
            }`}
          >
            <Icon
              name={row.on ? 'checkmark-circle' : 'minus-circle'}
              width={14}
              fill={
                row.on
                  ? 'var(--color-icon-success)'
                  : 'var(--color-icon-warning)'
              }
            />
            {row.name}
          </div>
        ))}
      </div>

      <div className='explore-graph__link' aria-hidden>
        <span>holds up</span>
      </div>

      <div className='explore-node explore-node--self'>{FEATURE}</div>

      <div className='explore-graph__link' aria-hidden>
        <span>holds up</span>
      </div>

      <div className='explore-graph__tier'>
        {DEPENDENTS.map((name) => (
          <div key={name} className='explore-node'>
            {name}
          </div>
        ))}
      </div>
    </div>

    <p className='explore-foot mt-3'>
      Nothing sits above the top row or below the bottom one: dependencies are
      only ever one layer deep.
    </p>
  </div>
)

/* ------------------------------------------------------------- stories -- */

const meta: Meta<typeof Checklist> = {
  component: Checklist,
  parameters: {
    docs: {
      description: {
        component:
          'Two ways of presenting the same relationship, against the table the tab ships with today. A reads the data as a condition — all of these must be on — which is what it is. C reads it as a shape, which is what the one-layer rule is about. Neither is built to ship.',
      },
    },
    layout: 'centered',
  },
  title: 'Explorations/Dependency layouts',
}
export default meta

type Story = StoryObj<typeof Checklist>

export const AChecklist: Story = {
  name: 'A · Checklist',
  render: () => <Checklist rows={PREREQUISITES} />,
}

export const AChecklistAtScale: Story = {
  name: 'A · Checklist, six prerequisites',
  render: () => <Checklist rows={MANY} />,
}

export const CNodes: Story = {
  name: 'C · Shape',
  render: () => <Node rows={PREREQUISITES} />,
}

export const CNodesAtScale: Story = {
  name: 'C · Shape, six prerequisites',
  render: () => <Node rows={MANY} />,
}
