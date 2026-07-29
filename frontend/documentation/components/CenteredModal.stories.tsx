import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import CenteredModal from 'components/base/CenteredModal'
import Button from 'components/base/forms/Button'

const meta: Meta<typeof CenteredModal> = {
  component: CenteredModal,
  parameters: {
    chromatic: { delay: 300 },
    docs: {
      description: {
        component:
          'Traditional centred modal sized to ~80% of the viewport, with a scrollable body. ' +
          'Unlike the global `openModal` drawer, it is fully declarative: the parent owns the ' +
          'open state and passes `isOpen`/`onClose`, with arbitrary children as the body.',
      },
    },
    layout: 'centered',
  },
  title: 'Components/Modals/CenteredModal',
}
export default meta

type Story = StoryObj<typeof CenteredModal>

export const Default: Story = {
  render: () => (
    <CenteredModal isOpen title='Create Metric' onClose={() => {}}>
      <p className='mb-0'>Modal body content goes here.</p>
    </CenteredModal>
  ),
}

export const WithFormContent: Story = {
  render: () => (
    <CenteredModal isOpen title='Create Metric' onClose={() => {}}>
      <div className='d-flex flex-column gap-4'>
        <div className='d-flex flex-column gap-1'>
          <label htmlFor='story-metric-name'>Name</label>
          <input
            id='story-metric-name'
            className='form-control'
            placeholder='e.g. Signup Completion Rate'
          />
        </div>
        <div className='d-flex flex-column gap-1'>
          <label htmlFor='story-metric-description'>Description</label>
          <input
            id='story-metric-description'
            className='form-control'
            placeholder='What does this metric measure?'
          />
        </div>
        <div className='d-flex justify-content-end gap-2'>
          <Button theme='secondary'>Cancel</Button>
          <Button>Create Metric</Button>
        </div>
      </div>
    </CenteredModal>
  ),
}

export const ScrollableBody: Story = {
  render: () => (
    <CenteredModal isOpen title='Terms of Service' onClose={() => {}}>
      <div className='d-flex flex-column gap-3'>
        {Array.from({ length: 30 }, (_, i) => (
          <p key={i} className='text-secondary mb-0'>
            Long content block {i + 1} — the modal body scrolls once content
            exceeds 75% of the viewport height.
          </p>
        ))}
      </div>
    </CenteredModal>
  ),
}

const InteractiveExample = () => {
  const [isOpen, setIsOpen] = useState(false)
  return (
    <>
      <Button onClick={() => setIsOpen(true)}>Open modal</Button>
      <CenteredModal
        isOpen={isOpen}
        title='Create Metric'
        onClose={() => setIsOpen(false)}
      >
        <p className='mb-0'>
          Close me via the header button or by clicking the backdrop.
        </p>
      </CenteredModal>
    </>
  )
}

export const Interactive: Story = {
  parameters: { chromatic: { disableSnapshot: true } },
  render: () => <InteractiveExample />,
}
