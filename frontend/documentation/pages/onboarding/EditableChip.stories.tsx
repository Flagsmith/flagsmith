import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import EditableChip from 'components/pages/onboarding/EditableChip'

const meta: Meta<typeof EditableChip> = {
  component: EditableChip,
  parameters: {
    docs: {
      description: {
        component:
          'An onboarding-local rename chip: the shared Chip shell + a GhostInput + a pencil. Commits on blur / Enter; an empty value reverts to the last good name; an optional `transform` normalises on commit (e.g. flag-name rules). Used in the onboarding header sentence. Feature-local — not a shared inline-edit primitive.',
      },
    },
    layout: 'centered',
  },
  title: 'Pages/Onboarding/EditableChip',
}
export default meta

type Story = StoryObj<typeof EditableChip>

// EditableChip is controlled; wrap it so the stories commit and re-render.
const Controlled = ({
  initial,
  label,
  transform,
}: {
  initial: string
  label: string
  transform?: (raw: string) => string
}) => {
  const [value, setValue] = useState(initial)
  return (
    <EditableChip
      label={label}
      value={value}
      onCommit={setValue}
      transform={transform}
    />
  )
}

export const Default: Story = {
  render: () => <Controlled label='Organisation' initial='Acme Inc' />,
}

export const Empty: Story = {
  render: () => <Controlled label='Project' initial='' />,
}

// Normalises on commit (spaces → underscores, lower-cased) like the flag chip.
export const WithTransform: Story = {
  render: () => (
    <Controlled
      label='Flag'
      initial='show_demo_button'
      transform={(raw) => raw.replace(/ /g, '_').toLowerCase()}
    />
  ),
}
