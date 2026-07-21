import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import InlineModal from 'components/InlineModal'
import Button from 'components/base/forms/Button'

const meta: Meta = {
  parameters: {
    chromatic: { delay: 300 },
    layout: 'centered',
  },
  title: 'Components/Modals/InlineModal',
}
export default meta

type Story = StoryObj

const Template = ({
  hideClose = false,
  showBack = false,
  title = 'Inline modal title',
  withBottom = false,
}: {
  hideClose?: boolean
  showBack?: boolean
  title?: string
  withBottom?: boolean
}) => (
  <div className='position-relative' style={{ minHeight: 280, width: 320 }}>
    <InlineModal
      title={title}
      isOpen
      onClose={() => {}}
      onBack={() => {}}
      showBack={showBack}
      hideClose={hideClose}
      bottom={withBottom ? <Button>Confirm</Button> : undefined}
    >
      <p className='mb-0'>This is the modal body content.</p>
    </InlineModal>
  </div>
)

export const Default: Story = {
  render: () => <Template />,
}

export const WithBackButton: Story = {
  render: () => <Template showBack title='Step 2 of 3' />,
}

export const WithBottomActions: Story = {
  render: () => <Template withBottom title='Confirm change' />,
}

export const HideClose: Story = {
  render: () => <Template hideClose title='Required action' />,
}
