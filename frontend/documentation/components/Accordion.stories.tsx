import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import Accordion from 'components/base/Accordion'
import Chip from 'components/base/Chip'
import Table, { TableBody, TableCell, TableRow } from 'components/base/Table'

const meta: Meta<typeof Accordion> = {
  args: {
    children: 'Description text',
    title: 'Accordion title',
  },
  component: Accordion,
  parameters: {
    chromatic: { disableSnapshot: false },
    docs: {
      description: {
        component:
          'A section that expands and collapses to show or hide its content. Use it to break long content into self-contained sections that are read one at a time. Avoid it where sections need comparing side by side, where hidden content is critical, or nested inside another accordion.',
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

// While its content loads: the header doesn't toggle.
export const Disabled: Story = {
  args: { defaultOpen: true, disabled: true },
}

// The title is a row, so a status can follow it; ms-auto pushes it to the end.
export const WithStatus: Story = {
  args: {
    title: (
      <>
        #3433 Enable new search
        <Chip className='ms-auto' size='xs'>
          Awaiting approval
        </Chip>
      </>
    ),
  },
}

export const Flush: Story = {
  args: {
    children: (
      <Table variant='ghost'>
        <TableBody>
          <TableRow>
            <TableCell>search_ranking</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>payment_provider</TableCell>
          </TableRow>
        </TableBody>
      </Table>
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

// An item in a list: no card border, and the list draws the dividers.
export const Row: Story = {
  args: { defaultOpen: true, variant: 'row' },
}

// Controlled, so a list can keep one item open at a time.
const OneOpenList = () => {
  const [openId, setOpenId] = React.useState<number | null>(1)
  return (
    <div>
      {[1, 2, 3].map((id) => (
        <Accordion
          key={id}
          variant='row'
          title={`Item ${id}`}
          open={openId === id}
          onOpenChange={(open) => setOpenId(open ? id : null)}
        >
          Content for item {id}
        </Accordion>
      ))}
    </div>
  )
}

export const OneOpenAtATime: Story = { render: () => <OneOpenList /> }
