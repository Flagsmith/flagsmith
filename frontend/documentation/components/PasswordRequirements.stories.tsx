import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import PasswordRequirements from 'components/PasswordRequirements'
import Input from 'components/base/forms/Input'

const meta: Meta = {
  parameters: {
    docs: {
      description: {
        component:
          'Checklist of password validation rules (length, numbers, special characters, casing) shown **below** a password input. Renders only the list — green for met, red for unmet — and reports the overall pass state via `onRequirementsMet`. The input is owned by the parent; the stories below pair one with the component to demonstrate real usage.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Feedback/PasswordRequirements',
}
export default meta

type Story = StoryObj

const Interactive = ({ initial = '' }: { initial?: string }) => {
  const [password, setPassword] = useState(initial)
  return (
    <div style={{ width: 320 }}>
      <Input
        type='password'
        value={password}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
          setPassword(e.target.value)
        }
        placeholder='Type a password'
      />
      <PasswordRequirements password={password} onRequirementsMet={() => {}} />
    </div>
  )
}

const sourceFor = (
  initial: string,
) => `const [password, setPassword] = useState(${JSON.stringify(initial)})

return (
  <>
    <Input
      type='password'
      value={password}
      onChange={(e) => setPassword(e.target.value)}
    />
    <PasswordRequirements
      password={password}
      onRequirementsMet={() => {}}
    />
  </>
)`

export const Empty: Story = {
  parameters: {
    docs: { source: { code: sourceFor(''), language: 'tsx' } },
  },
  render: () => <Interactive />,
}

export const PartiallyMet: Story = {
  parameters: {
    docs: { source: { code: sourceFor('abc'), language: 'tsx' } },
  },
  render: () => <Interactive initial='abc' />,
}

export const AllRequirementsMet: Story = {
  parameters: {
    docs: { source: { code: sourceFor('Str0ng!Pass'), language: 'tsx' } },
  },
  render: () => <Interactive initial='Str0ng!Pass' />,
}
