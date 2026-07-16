import type { Meta, StoryObj } from 'storybook'

import Drawer from 'components/base/Drawer'
import Button from 'components/base/forms/Button'

const meta: Meta<typeof Drawer> = {
  component: Drawer,
  parameters: {
    chromatic: { delay: 300 },
    docs: {
      description: {
        component:
          'Right-anchored drawer on the native `<dialog>` element (shares the DS ' +
          'Dialog chrome and slots). Full height, slides from the right, `width` ' +
          '`default` (800px) or `narrow` (640px). Use it for larger flows; use Dialog ' +
          'for centred, focused tasks.',
      },
    },
    layout: 'fullscreen',
  },
}

export default meta

type Story = StoryObj<typeof Drawer>

const noop = () => undefined

const body = (
  <p className='mb-0'>
    A drawer is for larger, multi-step flows anchored to the edge of the screen,
    as opposed to a centred modal for a single focused task.
  </p>
)

export const Default: Story = {
  render: () => (
    <Drawer open onClose={noop}>
      <Drawer.Header>Create feature</Drawer.Header>
      <Drawer.Body>{body}</Drawer.Body>
    </Drawer>
  ),
}

export const Narrow: Story = {
  render: () => (
    <Drawer open width='narrow' onClose={noop}>
      <Drawer.Header>Filters</Drawer.Header>
      <Drawer.Body>{body}</Drawer.Body>
    </Drawer>
  ),
}

export const WithFooter: Story = {
  render: () => (
    <Drawer open onClose={noop}>
      <Drawer.Header>Edit segment</Drawer.Header>
      <Drawer.Body>{body}</Drawer.Body>
      <Drawer.Footer>
        <Button theme='secondary'>Cancel</Button>
        <Button>Save</Button>
      </Drawer.Footer>
    </Drawer>
  ),
}
