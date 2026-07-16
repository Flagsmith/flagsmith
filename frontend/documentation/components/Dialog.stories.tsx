import type { Meta, StoryObj } from 'storybook'

import Dialog from 'components/base/Dialog'
import Button from 'components/base/forms/Button'

const meta: Meta<typeof Dialog> = {
  component: Dialog,
  parameters: {
    chromatic: { delay: 300 },
    docs: {
      description: {
        component:
          'DS dialog built on the native `<dialog>` element (`showModal()` top layer, ' +
          'built-in focus trap and Esc). Compound API: `Dialog.Header` / `Dialog.Body` / ' +
          '`Dialog.Footer`. Chrome is tokenised, so it themes light/dark with no bootstrap. ' +
          'The parent owns `open`; `onClose` fires on Esc, backdrop click, and the close button.',
      },
    },
    layout: 'fullscreen',
  },
}

export default meta

type Story = StoryObj<typeof Dialog>

const body = (
  <p className='mb-0'>
    This dialog renders in the browser top layer. Focus is trapped, Escape and a
    backdrop click both dismiss it, and the surface follows the active theme.
  </p>
)

const noop = () => undefined

export const Default: Story = {
  render: () => (
    <Dialog open size='md' onClose={noop}>
      <Dialog.Header>Rename flag</Dialog.Header>
      <Dialog.Body>{body}</Dialog.Body>
    </Dialog>
  ),
}

export const WithFooter: Story = {
  render: () => (
    <Dialog open size='sm' onClose={noop}>
      <Dialog.Header>Delete segment</Dialog.Header>
      <Dialog.Body>
        This can&apos;t be undone. The segment will be removed from every
        environment.
      </Dialog.Body>
      <Dialog.Footer>
        <Button theme='secondary'>Cancel</Button>
        <Button theme='danger'>Delete</Button>
      </Dialog.Footer>
    </Dialog>
  ),
}

export const Large: Story = {
  render: () => (
    <Dialog open size='lg' onClose={noop}>
      <Dialog.Header>Edit feature</Dialog.Header>
      <Dialog.Body>{body}</Dialog.Body>
    </Dialog>
  ),
}

export const Side: Story = {
  render: () => (
    <Dialog open size='side' onClose={noop}>
      <Dialog.Header>Create feature</Dialog.Header>
      <Dialog.Body>{body}</Dialog.Body>
    </Dialog>
  ),
}
