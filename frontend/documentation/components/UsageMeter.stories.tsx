import type { Meta, StoryObj } from 'storybook'
import UsageMeter from 'components/pages/usage/components/UsageMeter'

const meta: Meta<typeof UsageMeter> = {
  component: UsageMeter,
  parameters: { layout: 'padded' },
  title: 'Pages/Usage Dashboard/Components/UsageMeter',
}
export default meta

type Story = StoryObj<typeof UsageMeter>

export const UnderTheLimit: Story = {
  args: { limit: 2000000, total: 1240000 },
}

export const ApproachingTheLimit: Story = {
  args: { limit: 2000000, total: 1760000 },
}

export const AtTheLimit: Story = {
  args: { limit: 2000000, total: 2000000 },
}

export const OverTheLimit: Story = {
  args: { limit: 50000, total: 68400 },
}

// Nothing to be a percentage of, so the total stands on its own.
export const WithoutAPlanLimit: Story = {
  args: {
    limit: null,
    total: 340000,
  },
}

export const NoUsageYet: Story = {
  args: { limit: 50000, total: 0 },
}

export const WithANote: Story = {
  args: {
    limit: 2000000,
    note: (
      <p className='mt-3 mb-0 text-muted fs-small'>
        On track to use ~1.9M calls by the end of the period.
      </p>
    ),
    total: 1240000,
  },
}
