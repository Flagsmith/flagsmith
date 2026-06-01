import type { Meta, StoryObj } from 'storybook'

import IdentifierString from 'components/IdentifierString'

const meta: Meta<typeof IdentifierString> = {
  args: { value: 'my-feature-flag' },
  component: IdentifierString,
  parameters: { layout: 'centered' },
  title: 'Components/Data Display/IdentifierString',
}
export default meta

type Story = StoryObj<typeof IdentifierString>

export const Default: Story = {}

export const WithSpecialCharacters: Story = {
  args: { value: 'my feature flag' },
}
