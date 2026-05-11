import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import ModalDefault from 'components/modals/base/ModalDefault'

const meta: Meta = {
  parameters: {
    chromatic: { delay: 300 },
    docs: {
      description: {
        component:
          'Standard application modal — overlays a dialog with title, body, and dismiss controls. Open it from a trigger and pass `isOpen` plus close handlers (`onDismiss`, `toggle`); the parent owns the open state.',
      },
    },
    layout: 'centered',
  },
  title: 'Components/Modals/Modal',
}
export default meta

type Story = StoryObj

export const Default: Story = {
  render: () => (
    <ModalDefault
      isOpen
      onDismiss={() => {}}
      toggle={() => {}}
      title='Create Feature'
    >
      <p>Modal body content goes here.</p>
    </ModalDefault>
  ),
}
