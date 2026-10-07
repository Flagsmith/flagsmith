import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import Tag from 'components/tags/Tag'
import Constants from 'common/constants'
import { contentColourNames, contentColours } from 'common/theme/tokens'
import type { Tag as TTag } from 'common/types/responses'

const meta: Meta<typeof Tag> = {
  component: Tag,
  parameters: {
    chromatic: { disableSnapshot: false },
    docs: {
      description: {
        component:
          'A project tag. Custom tags take a fill from the design system Content palette, keyed on the colour stored on the tag so nothing needs migrating. System tags (Stale, GitHub, GitLab, Unhealthy) take no fill and carry their state in a coloured icon and their border rather than the fill, so the state survives for anyone who cannot tell the fills apart.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Tags/Tag',
}
export default meta

type Story = StoryObj<typeof Tag>

const tag = (over: Partial<TTag>): Partial<TTag> => ({
  color: Constants.tagColors[0],
  label: 'Checkout',
  type: 'NONE',
  ...over,
})

export const Custom: Story = { args: { tag: tag({}) } }

export const EveryColour: Story = {
  name: 'Every colour',
  render: () => (
    <div className='d-flex flex-wrap gap-1'>
      {contentColourNames.map((name) => (
        <Tag
          key={name}
          tag={tag({ color: contentColours[name], label: 'Checkout' })}
        />
      ))}
    </div>
  ),
}

// The VCS icon is keyed on the tag's label, which the integration sets, so the
// examples use labels it actually produces rather than the type name.
// No Unhealthy example: Tag returns null for it unless the feature_health flag
// is on, and Storybook's Utils stub answers false to every flag.
const SYSTEM_EXAMPLES: Partial<TTag>[] = [
  { label: 'Stale', type: 'STALE' },
  { label: 'PR Open', type: 'GITHUB' },
  { label: 'PR Merged', type: 'GITHUB' },
  { label: 'Issue Open', type: 'GITLAB' },
  { label: 'Issue Closed', type: 'GITLAB' },
]

export const SystemTags: Story = {
  name: 'System tags',
  render: () => (
    <div className='d-flex flex-wrap gap-1'>
      {SYSTEM_EXAMPLES.map((over) => (
        <Tag key={over.label} tag={tag(over)} />
      ))}
    </div>
  ),
}

// A colour we never issued, which the API allows. It takes the neutral rather
// than a guess: the label still reads, and the tag claims no category.
export const UnknownColour: Story = {
  args: { tag: tag({ color: '#123456', label: 'Set via API' }) },
  name: 'Colour outside the scale',
}

/** Hooks cannot live in a story's render, so selection state gets a component. */
const SelectableTags: React.FC = () => {
  const [picked, setPicked] = useState<string>('Checkout')
  return (
    <div className='d-flex flex-wrap gap-1'>
      {['Checkout', 'Billing', 'Search'].map((label, i) => (
        <Tag
          key={label}
          onClick={() => setPicked(label)}
          selected={picked === label}
          tag={tag({ color: Constants.tagColors[i], label })}
        />
      ))}
    </div>
  )
}

export const Selectable: Story = {
  render: () => <SelectableTags />,
}
