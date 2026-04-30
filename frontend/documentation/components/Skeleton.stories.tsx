import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import Skeleton from 'components/Skeleton'
import type { SkeletonProps } from 'components/Skeleton'

const meta: Meta<SkeletonProps> = {
  argTypes: {
    height: {
      control: 'number',
      description: 'Height of the skeleton element.',
    },
    variant: {
      control: 'select',
      description:
        'Shape variant. `text` for inline text placeholders, `badge` for pill shapes, `circle` for avatars and icons.',
      options: ['text', 'badge', 'circle'],
    },
    width: {
      control: 'number',
      description: 'Width of the skeleton element.',
    },
  },
  args: {
    variant: 'text',
    width: 200,
  },
  component: Skeleton,
  parameters: { layout: 'padded' },
  title: 'Components/Feedback/Skeleton',
}

export default meta

type Story = StoryObj<SkeletonProps>

// ---------------------------------------------------------------------------
// Default — interactive playground
// ---------------------------------------------------------------------------

export const Default: Story = {}

// ---------------------------------------------------------------------------
// Variants
// ---------------------------------------------------------------------------

export const Variants: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'Three shape variants for different content types. All include a shimmer animation that respects `prefers-reduced-motion`.',
      },
    },
  },
  render: () => (
    <div className='d-flex flex-column gap-3'>
      <div className='d-flex align-items-center gap-2'>
        <Skeleton variant='text' width={180} />
        <code>text</code> — default, 16px height, 4px radius
      </div>
      <div className='d-flex align-items-center gap-2'>
        <Skeleton variant='badge' width={80} height={20} />
        <code>badge</code> — pill shape, 12px radius
      </div>
      <div className='d-flex align-items-center gap-2'>
        <Skeleton variant='circle' width={32} height={32} />
        <code>circle</code> — round, for avatars and icons
      </div>
    </div>
  ),
}

// ---------------------------------------------------------------------------
// When to use
// ---------------------------------------------------------------------------

export const WhenToUse: Story = {
  name: 'When to use',
  parameters: {
    docs: {
      description: {
        story: `
**Use Skeleton when:**
- Loading data from an API and you want to show the layout shape before content arrives
- The content area has a predictable structure (list rows, cards, form fields)
- You want to reduce perceived loading time by showing a placeholder

**Don't use Skeleton when:**
- The loading state is brief (<200ms) — use a spinner instead
- The content structure is unpredictable — use a full-page spinner
- You're loading a single value — inline spinners work better

**Accessibility:**
- Shimmer animation respects \`prefers-reduced-motion: reduce\`
- Skeleton elements are decorative — screen readers skip them
        `,
      },
    },
  },
  render: () => (
    <div className='d-flex flex-column gap-2'>
      <Skeleton variant='text' width={220} />
      <Skeleton variant='text' width={160} />
      <Skeleton variant='text' width={190} />
    </div>
  ),
}

// ---------------------------------------------------------------------------
// Composition: Feature row skeleton
// ---------------------------------------------------------------------------

export const FeatureRowExample: Story = {
  name: 'Feature row example',
  parameters: {
    docs: {
      description: {
        story:
          'Compose multiple Skeleton elements to match the layout of a feature row. This mirrors what `FeatureRowSkeleton` renders.',
      },
    },
  },
  render: () => (
    <div className='d-flex align-items-center gap-3 px-2 py-3 border-bottom border-default'>
      <div className='d-flex flex-fill flex-column gap-1'>
        <div className='d-flex align-items-center gap-2'>
          <Skeleton variant='text' width={180} />
          <Skeleton variant='badge' width={60} height={20} />
        </div>
      </div>
      <Skeleton variant='text' width={100} />
      <Skeleton variant='circle' width={40} height={24} />
      <Skeleton variant='circle' width={32} height={32} />
    </div>
  ),
}

// ---------------------------------------------------------------------------
// Composition: Settings skeleton
// ---------------------------------------------------------------------------

export const SettingsExample: Story = {
  name: 'Settings example',
  parameters: {
    docs: {
      description: {
        story:
          'Compose Skeleton elements to match the layout of a settings section while data loads.',
      },
    },
  },
  render: () => (
    <div className='d-flex flex-column gap-4'>
      {[1, 2, 3].map((i) => (
        <div key={i} className='d-flex flex-column gap-2'>
          <div className='d-flex align-items-center gap-2'>
            <Skeleton variant='circle' width={40} height={24} />
            <Skeleton variant='text' width={200} />
          </div>
          <Skeleton variant='text' width={400} />
        </div>
      ))}
    </div>
  ),
}
