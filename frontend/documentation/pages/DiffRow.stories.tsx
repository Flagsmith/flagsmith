import type { Meta, StoryObj } from 'storybook'

import DiffRow from 'components/diff/DiffRow'

const meta: Meta<typeof DiffRow> = {
  component: DiffRow,
  parameters: {
    docs: {
      description: {
        component:
          'One row of a diff: a marker cell beside the content that changed. ' +
          'Used by DiffEnabled and DiffString for the rows we build ourselves.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Diff/DiffRow',
}

export default meta

type Story = StoryObj<typeof DiffRow>

export const Removed: Story = {
  args: { children: 'banner_size: small', state: 'removed' },
}

export const Added: Story = {
  args: { children: 'banner_size: large', state: 'added' },
}

export const Unchanged: Story = {
  args: { children: 'banner_size: large', state: 'unchanged' },
}

export const Stacked: Story = {
  render: () => (
    <>
      <DiffRow state='removed'>banner_size: small</DiffRow>
      <DiffRow state='added'>banner_size: large</DiffRow>
    </>
  ),
}

export const LongContentScrolls: Story = {
  args: {
    children: 'banner_size: '.repeat(40),
    scrollable: true,
    state: 'unchanged',
  },
}
