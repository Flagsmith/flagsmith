import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import ToggleChip from 'components/ToggleChip'

const meta: Meta<typeof ToggleChip> = {
  args: { active: false, children: 'Feature flag' },
  component: ToggleChip,
  parameters: {
    docs: {
      description: {
        component:
          'A selectable chip with a leading checkbox. It holds no palette: colour arrives as token utilities in className, so a tag hands it a validated swatch pair rather than a hex to derive from.',
      },
    },
    layout: 'centered',
  },
  title: 'Components/Data Display/ToggleChip',
}
export default meta

type Story = StoryObj<typeof ToggleChip>

const Interactive = (args: React.ComponentProps<typeof ToggleChip>) => {
  const [active, setActive] = useState(args.active ?? false)
  return (
    <ToggleChip {...args} active={active} onClick={() => setActive(!active)} />
  )
}

export const Default: Story = {
  render: (args: React.ComponentProps<typeof ToggleChip>) => (
    <Interactive {...args} />
  ),
}

export const AllStates: Story = {
  parameters: { chromatic: { disableSnapshot: false } },
  render: () => (
    <div className='d-flex gap-2'>
      <ToggleChip active>Active</ToggleChip>
      <ToggleChip>Inactive</ToggleChip>
      <ToggleChip active className='tag-green border-0'>
        Swatch, active
      </ToggleChip>
      <ToggleChip className='tag-green border-0'>Swatch</ToggleChip>
    </div>
  ),
}
