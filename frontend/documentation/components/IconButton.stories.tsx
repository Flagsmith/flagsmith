import type { Meta, StoryObj } from 'storybook'

import IconButton from 'components/base/IconButton'
import Icon from 'components/icons/Icon'

const meta: Meta<typeof IconButton> = {
  args: {
    'aria-label': 'Add',
    children: <Icon name='plus' width={24} />,
  },
  component: IconButton,
  parameters: {
    docs: {
      description: {
        component:
          'An icon-only button, separate from Button, which stays text-only. Five variants and three sizes. The design system frame draws the 44px `large` only; `medium`, `small` and the `ghost` variant are ours, for rows too dense for a 44px square. `aria-label` is required at the type level, because there is no label to read.',
      },
    },
  },
  title: 'Components/Forms/IconButton',
}
export default meta

type Story = StoryObj<typeof IconButton>

export const Primary: Story = {}

export const Secondary: Story = {
  args: { variant: 'secondary' },
}

export const Outline: Story = {
  args: { variant: 'outline' },
}

export const Ghost: Story = {
  args: { variant: 'ghost' },
}

export const Destructive: Story = {
  args: {
    'aria-label': 'Delete',
    children: <Icon name='trash-2' width={24} />,
    variant: 'destructive',
  },
}

export const Disabled: Story = {
  render: () => (
    <div className='d-flex gap-3'>
      <IconButton aria-label='Add' disabled>
        <Icon name='plus' width={24} />
      </IconButton>
      <IconButton aria-label='Add' disabled variant='secondary'>
        <Icon name='plus' width={24} />
      </IconButton>
      <IconButton aria-label='Add' disabled variant='outline'>
        <Icon name='plus' width={24} />
      </IconButton>
      <IconButton aria-label='Delete' disabled variant='destructive'>
        <Icon name='trash-2' width={24} />
      </IconButton>
    </div>
  ),
}

export const AllVariants: Story = {
  render: () => (
    <div className='d-flex gap-3 align-items-center'>
      <IconButton aria-label='Add'>
        <Icon name='plus' width={24} />
      </IconButton>
      <IconButton aria-label='Add' variant='secondary'>
        <Icon name='plus' width={24} />
      </IconButton>
      <IconButton aria-label='Add' variant='outline'>
        <Icon name='plus' width={24} />
      </IconButton>
      <IconButton aria-label='Delete' variant='destructive'>
        <Icon name='trash-2' width={24} />
      </IconButton>
    </div>
  ),
}

export const Sizes: Story = {
  render: () => (
    <div className='d-flex gap-3 align-items-center'>
      <IconButton aria-label='Add' size='small'>
        <Icon name='plus' width={16} />
      </IconButton>
      <IconButton aria-label='Add' size='medium'>
        <Icon name='plus' width={20} />
      </IconButton>
      <IconButton aria-label='Add' size='large'>
        <Icon name='plus' width={24} />
      </IconButton>
    </div>
  ),
}

export const GhostInARow: Story = {
  render: () => (
    <div style={{ maxWidth: 360 }}>
      {['show_demo_3', 'test_repro_mv_display', 'config_feat_test'].map(
        (name) => (
          <div
            key={name}
            className='d-flex align-items-center justify-content-between py-1'
          >
            <span>{name}</span>
            <IconButton
              aria-label={`Remove ${name}`}
              size='medium'
              variant='ghost'
            >
              <Icon name='trash-2' width={20} />
            </IconButton>
          </div>
        ),
      )}
    </div>
  ),
}
