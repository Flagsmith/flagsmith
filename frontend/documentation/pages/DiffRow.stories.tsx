import type { Meta, StoryObj } from 'storybook'

import DiffRow from 'components/diff/DiffRow'

const meta: Meta<typeof DiffRow> = {
  component: DiffRow,
  parameters: {
    // Snapshotted in both themes: these rows carry the added/removed colours
    // for every diff we render ourselves.
    chromatic: { disableSnapshot: false },
    docs: {
      description: {
        component:
          'One row of a diff: a marker cell beside the content that changed. ' +
          'Used for the rows we build ourselves, in DiffEnabled and ' +
          'DiffString. The rows react-diff-viewer renders are styled ' +
          'separately. Toggle the theme in the toolbar to QA.',
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

// No marker glyph, and the content sits on the code surface.
export const Unchanged: Story = {
  args: { children: 'banner_size: large', state: 'unchanged' },
}

// The pair as DiffEnabled and DiffString render them, one above the other.
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
