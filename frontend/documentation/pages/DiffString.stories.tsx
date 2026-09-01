import type { Meta, StoryObj } from 'storybook'

import DiffString from 'components/diff/DiffString'

const meta: Meta<typeof DiffString> = {
  component: DiffString,
  parameters: {
    docs: {
      description: {
        component:
          'The diff view for flag values (react-diff-viewer + Prism for JSON). ' +
          'Uses the same code colour tokens as the Highlight component, so it ' +
          'follows light/dark mode. Toggle the theme in the toolbar to QA.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Diff/DiffString',
}

export default meta

type Story = StoryObj<typeof DiffString>

const oldJson = `{
  "id": "london-js",
  "title": "Hello London.js!",
  "description": "Join us at London.js and get insights on best practices!",
  "buttonText": "Register on Meetup",
  "isClosable": false
}`

const newJson = `{
  "id": "london-js",
  "title": "Hello London.js!",
  "description": "Join us at London.js!",
  "buttonText": "Register now",
  "isClosable": true
}`

export const ChangedJson: Story = {
  args: { newValue: newJson, oldValue: oldJson },
}

export const ChangedString: Story = {
  args: { newValue: 'banner_size: large', oldValue: 'banner_size: small' },
}

export const SameJson: Story = {
  args: { newValue: oldJson, oldValue: oldJson },
}

// An empty old value renders as `""`, not a blank row.
export const FromEmpty: Story = {
  args: { newValue: 'banner_size: large', oldValue: '' },
}
