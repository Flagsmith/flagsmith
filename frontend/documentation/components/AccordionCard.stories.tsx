import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import AccordionCard from 'components/base/accordion/AccordionCard'

const meta: Meta = {
  parameters: {
    docs: {
      description: {
        component:
          'Collapsible card with a header, chevron toggle, and animated body. Use `defaultOpen` to start expanded and `isLoading` to show a spinner in place of content while fetching.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Patterns/AccordionCard',
}
export default meta

type Story = StoryObj

export const Default: Story = {
  render: () => (
    <AccordionCard title='Summary'>
      <p className='mb-0'>Accordion content goes here.</p>
    </AccordionCard>
  ),
}

export const DefaultOpen: Story = {
  render: () => (
    <AccordionCard title='Details' defaultOpen>
      <p className='mb-0'>This accordion starts open.</p>
    </AccordionCard>
  ),
}
