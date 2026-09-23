import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import ContentCard from 'components/base/grid/ContentCard'
import Button from 'components/base/forms/Button'

const meta: Meta<typeof ContentCard> = {
  component: ContentCard,
  parameters: {
    docs: {
      description: {
        component:
          'A surface card with an optional title and action slot. Used as a section container in wizards and detail pages.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Grid/ContentCard',
}
export default meta

type Story = StoryObj<typeof ContentCard>

export const Default: Story = {
  render: () => (
    <ContentCard title='Experiment details'>
      <p className='text-muted fs-small mb-0'>
        Name the experiment and capture what you&apos;re trying to learn before
        picking a flag.
      </p>
    </ContentCard>
  ),
}

export const WithAction: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'Pass an `action` node to render a button or link in the card header.',
      },
    },
  },
  render: () => (
    <ContentCard
      title='Feature flag'
      action={
        <Button theme='primary' size='small'>
          Edit
        </Button>
      }
    >
      <p className='text-muted fs-small mb-0'>
        The flag you&apos;re experimenting on. Variations are read-only, defined
        on the flag itself.
      </p>
    </ContentCard>
  ),
}

export const NoTitle: Story = {
  parameters: {
    docs: {
      description: {
        story: 'Without a title, the card renders as a plain content surface.',
      },
    },
  },
  render: () => (
    <ContentCard>
      <p className='mb-0'>
        This card has no header — just content inside a bordered surface.
      </p>
    </ContentCard>
  ),
}
