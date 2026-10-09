import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import Accordion from 'components/base/Accordion'
import Chip from 'components/base/Chip'

const meta: Meta<typeof Accordion> = {
  args: {
    children: <p className='mb-0'>Accordion content goes here.</p>,
    title: 'Accordion title',
  },
  component: Accordion,
  parameters: {
    chromatic: { disableSnapshot: false },
    docs: {
      description: {
        component:
          'A section that expands and collapses to show or hide its content. Use it to break long content into self-contained sections that are read one at a time. Avoid it where sections need comparing side by side, where hidden content is critical, or nested inside another accordion. Figma: Flagsmith DEV-Ready, Accordion (151:7090).',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Data Display/Accordion',
}
export default meta

type Story = StoryObj<typeof Accordion>

export const Default: Story = {}

export const Open: Story = {
  args: { defaultOpen: true },
}

export const WithDescription: Story = {
  args: { defaultOpen: true, description: 'Description text' },
}

export const WithMeta: Story = {
  args: {
    meta: <Chip size='xs'>Awaiting approval</Chip>,
    title: '#3433 Enable new search',
  },
}

export const Flush: Story = {
  args: {
    children: (
      <table className='table mb-0'>
        <tbody>
          <tr>
            <td>search_ranking</td>
          </tr>
          <tr>
            <td>payment_provider</td>
          </tr>
        </tbody>
      </table>
    ),
    defaultOpen: true,
    flush: true,
  },
}

export const Group: Story = {
  render: () => (
    <div className='d-flex flex-column gap-2'>
      <Accordion title='Billing' defaultOpen>
        <p className='mb-0'>Plans, invoices and payment methods.</p>
      </Accordion>
      <Accordion title='Members'>
        <p className='mb-0'>People and groups in this organisation.</p>
      </Accordion>
      <Accordion title='Integrations'>
        <p className='mb-0'>Connected tools.</p>
      </Accordion>
    </div>
  ),
}
