import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import TagColourPicker from 'components/tags/TagColourPicker'
import Constants from 'common/constants'

const meta: Meta<typeof TagColourPicker> = {
  component: TagColourPicker,
  parameters: {
    chromatic: { disableSnapshot: false },
    docs: {
      description: {
        component:
          "The swatch grid a custom tag picks its colour from, shared by the create/edit form and the inline picker. Each swatch is a `Tag` with no label, so the grid sizes it: without that it collapses to the chip's minimum width and reads as a sliver. Colours come from the design system's Content palette and are fixed rather than theme-aware, because a chip carries its own surface.",
      },
    },
    layout: 'padded',
  },
  title: 'Components/Forms/TagColourPicker',
}
export default meta

type Story = StoryObj<typeof TagColourPicker>

export const Default: Story = {
  args: { value: Constants.tagColors[0] },
}

export const NothingSelected: Story = {
  args: { value: undefined },
  name: 'Nothing selected',
}

/** Hooks cannot live in a story's render, so selection state gets a component. */
const PickerWithState: React.FC = () => {
  const [colour, setColour] = useState<string>(Constants.tagColors[4])
  return (
    <div className='d-flex flex-column gap-3'>
      <TagColourPicker onChange={setColour} value={colour} />
      <code className='text-secondary'>{colour}</code>
    </div>
  )
}

export const Interactive: Story = {
  name: 'Picking a colour',
  render: () => <PickerWithState />,
}
