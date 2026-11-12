import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import ToggleChip from 'components/base/ToggleChip'
import { TAG_COLOURS } from 'common/theme/tagColours'

const meta: Meta<typeof ToggleChip> = {
  component: ToggleChip,
  parameters: { layout: 'centered' },
  title: 'Components/Forms/ToggleChip',
}
export default meta

type Story = StoryObj<typeof ToggleChip>

const Group = () => {
  const [selected, setSelected] = useState<string[]>(['Production'])
  return (
    <div role='group' aria-label='Environments' className='d-flex gap-2'>
      {['Production', 'Staging', 'Development'].map((name, i) => (
        <ToggleChip
          key={name}
          checked={selected.includes(name)}
          onChange={(checked) =>
            setSelected(
              checked
                ? [...selected, name]
                : selected.filter((s) => s !== name),
            )
          }
          colour={TAG_COLOURS[i + 1]}
        >
          {name}
        </ToggleChip>
      ))}
    </div>
  )
}

export const Default: Story = {
  render: () => <Group />,
}

export const States: Story = {
  render: () => (
    <div className='d-flex gap-2'>
      <ToggleChip checked={false} onChange={() => {}}>
        Unchecked
      </ToggleChip>
      <ToggleChip checked onChange={() => {}}>
        Checked
      </ToggleChip>
      <ToggleChip checked={false} disabled onChange={() => {}}>
        Disabled
      </ToggleChip>
    </div>
  ),
}
