import type { Meta, StoryObj } from 'storybook'

import DiffEnabled from 'components/diff/DiffEnabled'

const meta: Meta<typeof DiffEnabled> = {
  component: DiffEnabled,
  parameters: {
    // Snapshotted in both themes: these rows carry the added/removed colours
    // for every boolean change in the audit log and change-request review.
    chromatic: { disableSnapshot: false },
    docs: {
      description: {
        component:
          'The diff view for a flag or segment override being turned on or ' +
          'off. Hand-built rather than react-diff-viewer, but shares its ' +
          'added/removed row colours. Toggle the theme in the toolbar to QA.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Diff/DiffEnabled',
}

export default meta

type Story = StoryObj<typeof DiffEnabled>

export const OffToOn: Story = {
  args: { newValue: true, oldValue: false },
}

export const OnToOff: Story = {
  args: { newValue: false, oldValue: true },
}

// Unchanged renders a single switch with no diff colours at all.
export const Unchanged: Story = {
  args: { newValue: true, oldValue: true },
}
