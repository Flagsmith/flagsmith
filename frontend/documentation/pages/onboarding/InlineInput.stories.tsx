import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import InlineInput from 'components/pages/onboarding/InlineInput'

const meta: Meta<typeof InlineInput> = {
  component: InlineInput,
  parameters: {
    docs: {
      description: {
        component:
          'An onboarding-local inline editable value (GhostInput + pencil) used in the welcome sentence. Reads as part of the prose - a dashed underline hints it’s editable - rather than a pill. Commits on blur / Enter; an empty value reverts; an optional `transform` normalises on commit (e.g. flag-name rules). Feature-local - not a shared inline-edit primitive.',
      },
    },
    layout: 'centered',
  },
  title: 'Pages/Onboarding/InlineInput',
}
export default meta

type Story = StoryObj<typeof InlineInput>

// InlineInput is controlled; wrap it so the stories commit and re-render.
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
    <InlineInput
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
