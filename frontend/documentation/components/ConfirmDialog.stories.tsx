import type { Meta, StoryObj } from 'storybook'

import { ConfirmDialog } from 'components/base/Dialog'

const meta: Meta<typeof ConfirmDialog> = {
  component: ConfirmDialog,
  parameters: {
    chromatic: { delay: 300 },
    docs: {
      description: {
        component:
          'Small Dialog preset for yes/no confirmations. Backs the imperative ' +
          '`openConfirm`, and is usable declaratively for new code.',
      },
    },
    layout: 'fullscreen',
  },
}

export default meta

type Story = StoryObj<typeof ConfirmDialog>

const noop = () => undefined

export const Default: Story = {
  render: () => (
    <ConfirmDialog
      open
      title='Leave without saving?'
      onYes={noop}
      onNo={noop}
      yesText='Discard'
    >
      You have unsaved changes. Are you sure you want to leave?
    </ConfirmDialog>
  ),
}

export const Destructive: Story = {
  render: () => (
    <ConfirmDialog
      open
      destructive
      title='Delete segment'
      yesText='Delete'
      onYes={noop}
      onNo={noop}
    >
      This can&apos;t be undone. The segment will be removed from every
      environment.
    </ConfirmDialog>
  ),
}
