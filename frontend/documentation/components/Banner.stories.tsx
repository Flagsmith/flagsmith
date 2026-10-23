import type { Meta, StoryObj } from 'storybook'

import Banner from 'components/base/Banner'
import Button from 'components/base/forms/Button'

const meta: Meta<typeof Banner> = {
  args: {
    children: 'Description text',
    title: 'Info banner',
    type: 'info',
  },
  component: Banner,
  parameters: {
    docs: {
      description: {
        component:
          'Keeps users informed when there is an update or a status change they should know about. Four types: info, success, warning and error. The border and title carry the type; the body stays in default text. Use it for system feedback and for the outcome of an action, not for frequent messages, which become noise.',
      },
    },
  },
  title: 'Components/Feedback/Banner',
}
export default meta

type Story = StoryObj<typeof Banner>

export const Info: Story = {}

export const Success: Story = {
  args: {
    children: 'Description text',
    title: 'Info success',
    type: 'success',
  },
}

export const Warning: Story = {
  args: {
    children: 'Description text',
    title: 'Info warning',
    type: 'warning',
  },
}

export const Error: Story = {
  args: { children: 'Description text', title: 'Info error', type: 'error' },
}

export const WithoutTitle: Story = {
  args: {
    children: 'A single line, for when there is nothing to summarise.',
    title: undefined,
  },
}

export const WithAction: Story = {
  args: {
    action: (
      <Button size='small' theme='outline'>
        Review
      </Button>
    ),
    children: 'Two prerequisites are not currently met.',
    title: 'Serving its disabled value',
    type: 'warning',
  },
}

export const AllTypes: Story = {
  render: () => (
    <div className='d-flex flex-column gap-3' style={{ maxWidth: 420 }}>
      <Banner type='info' title='Info banner'>
        Description text
      </Banner>
      <Banner type='success' title='Info success'>
        Description text
      </Banner>
      <Banner type='warning' title='Info warning'>
        Description text
      </Banner>
      <Banner type='error' title='Info error'>
        Description text
      </Banner>
    </div>
  ),
}
