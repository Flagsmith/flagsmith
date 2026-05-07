import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import ToggleChip from 'components/ToggleChip'
import {
  colorChart2,
  colorChart3,
  colorSurfaceAction,
} from 'common/theme/tokens'

const meta: Meta<typeof ToggleChip> = {
  argTypes: {
    color: { control: 'color' },
  },
  args: { active: false, children: 'Feature flag', color: colorSurfaceAction },
  component: ToggleChip,
  parameters: { layout: 'centered' },
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
  render: () => (
    <div className='d-flex gap-2'>
      <ToggleChip color={colorSurfaceAction} active>
        Active
      </ToggleChip>
      <ToggleChip color={colorSurfaceAction}>Inactive</ToggleChip>
      <ToggleChip color={colorChart2} active>
        Danger
      </ToggleChip>
      <ToggleChip color={colorChart3}>Success</ToggleChip>
    </div>
  ),
}
