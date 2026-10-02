import type { Meta, StoryObj } from 'storybook'

import IconButton from 'components/base/IconButton'
import Icon from 'components/icons/Icon'
import './DependencyPresentations.scss'

// Explorations only, none of these ships as-is. Four ways to present the same
// data, built on the real numbers from a project where most prerequisites are
// off, which is the case the shipped table reads worst in.

type Flag = { name: string; on: boolean }

const FEATURE = '0000001_test_multi'
const ENVIRONMENT = 'Development'

const ROWS: Flag[] = [
  { name: 'show_demo_3', on: true },
  { name: 'test_repro_mv_display', on: false },
  { name: 'show_demo_f', on: true },
  { name: 'test_feat_with_value', on: false },
  { name: '0002_test_multi', on: false },
  { name: 'test', on: false },
  { name: 'config_feat_test', on: false },
  { name: 'test_featvalue', on: false },
  { name: 'new_feat', on: false },
]

const offCount = ROWS.filter((row) => !row.on).length

const Remove = ({ name }: { name: string }) => (
  <IconButton aria-label={`Remove ${name}`} size='medium' variant='ghost'>
    <Icon name='trash-2' width={20} />
  </IconButton>
)

const State = ({ on }: { on: boolean }) => (
  <span className={`pres-state pres-state--${on ? 'on' : 'off'}`}>
    <Icon name={on ? 'checkmark-circle' : 'minus-circle'} width={16} />
    {on ? 'On' : 'Off'}
  </span>
)

// Borrows the toggle's silhouette without being a control: a span, not a
// button, at full contrast rather than rc-switch's disabled grey. Reads as the
// product's language for flag state, with nothing inviting a click.
const StateToggle = ({ on }: { on: boolean }) => (
  <span className='pres-toggle-state'>
    <span
      className={`pres-toggle pres-toggle--${on ? 'on' : 'off'}`}
      role='img'
      aria-label={on ? 'On' : 'Off'}
    />
    {on ? 'On' : 'Off'}
  </span>
)

/* -------------------------------------------------- 1 · Resolved state -- */

const ResolvedState = ({ toggle }: { toggle?: boolean } = {}) => (
  <div className='pres'>
    <h5 className='mb-3'>Prerequisites</h5>

    <div className='pres-resolved'>
      <div>
        <div className='pres-resolved__env'>{ENVIRONMENT}</div>
        <div className='pres-resolved__value'>
          <Icon name='minus-circle' width={20} />
          Serving off
        </div>
      </div>
      <div className='pres-resolved__why'>
        {offCount} of {ROWS.length} prerequisites are off
      </div>
    </div>

    <div className='pres-panel'>
      {ROWS.map((row) => (
        <div className='pres-row' key={row.name}>
          <span className='pres-row__name'>{row.name}</span>
          {toggle ? <StateToggle on={row.on} /> : <State on={row.on} />}
          <Remove name={row.name} />
        </div>
      ))}
    </div>
  </div>
)

/* ------------------------------------------------------- 2 · Gate ------- */

const Gate = () => (
  <div className='pres'>
    <h5 className='mb-3'>Prerequisites</h5>

    <div className='pres-gate'>
      <ul className='pres-gate__inputs'>
        {ROWS.map((row) => (
          <li
            key={row.name}
            className={`pres-gate__input pres-gate__input--${
              row.on ? 'on' : 'off'
            }`}
          >
            <span className='pres-gate__name'>{row.name}</span>
            <span className='pres-gate__dot' />
          </li>
        ))}
      </ul>

      <div className='pres-gate__bus' />

      <div className='pres-gate__op'>AND</div>

      <div className='pres-gate__out'>
        <div className='pres-gate__feature'>{FEATURE}</div>
        <div className='pres-gate__result'>serving off</div>
      </div>
    </div>
  </div>
)

/* ---------------------------------------------------- 3 · Grouped ------- */

const Grouped = () => {
  const off = ROWS.filter((row) => !row.on)
  const on = ROWS.filter((row) => row.on)

  return (
    <div className='pres'>
      <h5 className='mb-3'>Prerequisites</h5>

      <div className='pres-group'>
        <div className='pres-group__head pres-group__head--off'>
          <Icon name='minus-circle' width={16} />
          Holding {FEATURE} back
          <span className='pres-group__count'>{off.length}</span>
        </div>
        <div className='pres-panel'>
          {off.map((row) => (
            <div className='pres-row' key={row.name}>
              <span className='pres-row__name'>{row.name}</span>
              <Remove name={row.name} />
            </div>
          ))}
        </div>
      </div>

      <div className='pres-group'>
        <div className='pres-group__head'>
          <Icon name='checkmark-circle' width={16} />
          Satisfied
          <span className='pres-group__count'>{on.length}</span>
        </div>
        <div className='pres-panel'>
          {on.map((row) => (
            <div className='pres-row' key={row.name}>
              <span className='pres-row__name'>{row.name}</span>
              <Remove name={row.name} />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

/* ------------------------------------------------------- 4 · Split ------ */

const Split = () => (
  <div className='pres'>
    <div className='pres-split'>
      <section>
        <h5 className='mb-1'>Gated by</h5>
        <p className='text-muted pres-split__sub'>
          {FEATURE} only serves its own value when all of these are on.
        </p>
        <div className='pres-panel'>
          {ROWS.slice(0, 4).map((row) => (
            <div className='pres-row' key={row.name}>
              <span className='pres-row__name'>{row.name}</span>
              <State on={row.on} />
            </div>
          ))}
        </div>
      </section>

      {/* Only ever one of these two has rows: a feature is a dependent or a
          prerequisite, never both. The split makes that visible. */}
      <section className='pres-split__empty'>
        <h5 className='mb-1'>Gates</h5>
        <p className='text-muted pres-split__sub'>
          Nothing depends on {FEATURE}.
        </p>
        <div className='pres-panel pres-panel--empty'>
          <Icon name='layers' width={24} />
          <span>
            A flag with prerequisites cannot be a prerequisite itself.
          </span>
        </div>
      </section>
    </div>
  </div>
)

/* ------------------------------------------------------------------------ */

const meta: Meta = {
  parameters: {
    docs: {
      description: {
        component:
          'Four presentations of the same prerequisites, explored against a flag whose prerequisites are mostly off. Explorations, not shipped components.',
      },
    },
  },
  title: 'Explorations/Dependency presentations',
}
export default meta

type Story = StoryObj

export const OneResolvedState: Story = {
  name: '1 · Resolved state header',
  render: () => <ResolvedState />,
}

export const OneResolvedStateToggle: Story = {
  name: '1b · Resolved state, toggle indicator',
  render: () => <ResolvedState toggle />,
}

export const TwoGate: Story = {
  name: '2 · Gate diagram',
  render: () => <Gate />,
}

export const ThreeGrouped: Story = {
  name: '3 · Grouped by state',
  render: () => <Grouped />,
}

export const FourSplit: Story = {
  name: '4 · Side-by-side halves',
  render: () => <Split />,
}
