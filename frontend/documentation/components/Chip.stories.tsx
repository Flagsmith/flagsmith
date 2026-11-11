import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import Chip from 'components/base/Chip'
import ColorSwatch from 'components/ColorSwatch'
import { colorChart1, colorChart3 } from 'common/theme/tokens'

const meta: Meta<typeof Chip> = {
  args: { children: 'Production' },
  component: Chip,
  parameters: {
    chromatic: { disableSnapshot: false },
    docs: {
      description: {
        component:
          'Canonical token-based chip primitive: a small labelled pill token. Layout via Bootstrap utilities, colour/radius via token utilities, padding/sizes/border/truncation in SCSS. Leading/trailing icons go in as children. Pass `checked` and `onChange` for a toggle: a hidden native checkbox, accent styling and a tick when checked. Count badges are a separate Badge concern. The legacy `.chip` (old SCSS vars + manual dark-mode block, ~35×) migrates onto this under #6606.',
      },
    },
    layout: 'centered',
  },
  title: 'Components/Data Display/Chip',
}
export default meta

type Story = StoryObj<typeof Chip>

export const Neutral: Story = {}

export const Accent: Story = {
  args: { children: '"hello"', variant: 'accent' },
}

export const Sizes: Story = {
  render: () => (
    <div className='d-flex align-items-center gap-2'>
      <Chip size='default'>Default</Chip>
      <Chip size='sm'>Small</Chip>
      <Chip size='xs'>Extra small</Chip>
    </div>
  ),
}

export const Removable: Story = {
  args: { children: 'feature-flag', onRemove: () => undefined },
}

export const Truncated: Story = {
  args: {
    children: '{ "test": "testvalue-that-keeps-going-and-going" }',
    truncate: true,
    variant: 'accent',
  },
}

export const Group: Story = {
  render: () => (
    <div className='d-flex flex-wrap gap-2'>
      <Chip>Development</Chip>
      <Chip variant='accent'>Staging</Chip>
      <Chip onRemove={() => undefined}>Production</Chip>
    </div>
  ),
}

export const Toggle: Story = {
  render: () => {
    const ToggleGroup = () => {
      const [selected, setSelected] = useState(['Production'])
      const toggle = (name: string, checked: boolean) =>
        setSelected(
          checked ? [...selected, name] : selected.filter((s) => s !== name),
        )
      return (
        <div className='d-flex flex-wrap gap-2'>
          {[
            { colour: colorChart1, name: 'Production' },
            { colour: colorChart3, name: 'Development' },
          ].map(({ colour, name }) => (
            <Chip
              key={name}
              checked={selected.includes(name)}
              onChange={(checked) => toggle(name, checked)}
            >
              <ColorSwatch color={colour} shape='circle' size='sm' />
              {name}
            </Chip>
          ))}
        </div>
      )
    }
    return <ToggleGroup />
  },
}

export const ToggleStates: Story = {
  render: () => (
    <div className='d-flex flex-wrap gap-2'>
      <Chip checked onChange={() => undefined}>
        Checked
      </Chip>
      <Chip checked={false} onChange={() => undefined}>
        Unchecked
      </Chip>
    </div>
  ),
}
