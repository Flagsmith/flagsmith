import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import ValueEditor from 'components/ValueEditor'
import FieldLabel from 'components/base/forms/FieldLabel'
import Constants from 'common/constants'

const meta: Meta = {
  parameters: { chromatic: { disableSnapshot: false } },
  title: 'Components/Forms/ValueEditor',
}
export default meta

type Story = StoryObj

const DEFAULT_TOOLTIP = Constants.strings.REMOTE_CONFIG_DESCRIPTION

const Interactive = ({
  initialValue = '',
  label,
  tooltip = DEFAULT_TOOLTIP,
  ...props
}: Record<string, any>) => {
  const [value, setValue] = useState(initialValue)
  return (
    <div style={{ maxWidth: 640, paddingTop: 24 }}>
      {label && <FieldLabel tooltip={tooltip}>{label}</FieldLabel>}
      <ValueEditor {...props} value={value} onChange={setValue} />
    </div>
  )
}

export const Default: Story = {
  render: () => <Interactive label='Value' />,
}

export const WithValue: Story = {
  render: () => <Interactive label='Value' initialValue='DEFAULT_VALUE' />,
}

export const Multiline: Story = {
  render: () => (
    <Interactive
      label='Value'
      initialValue={
        'a-long-single-line-value-that-runs-under-the-copy-button-if-unpadded\nsecond line\nthird line'
      }
    />
  ),
}

export const Json: Story = {
  render: () => (
    <Interactive
      label='Value'
      language='json'
      initialValue='{ "colour": "blue", "size": 12 }'
    />
  ),
}

export const InvalidJson: Story = {
  render: () => (
    <Interactive label='Value' language='json' initialValue='{ "colour": ' />
  ),
}

export const CodeMedium: Story = {
  render: () => (
    <Interactive
      label='Variation Value'
      tooltip={Constants.strings.REMOTE_CONFIG_DESCRIPTION_VARIATION}
      className='code-medium'
      initialValue='variant-a'
    />
  ),
}

export const Disabled: Story = {
  render: () => (
    <Interactive label='Control value' disabled initialValue='DEFAULT_VALUE' />
  ),
}

export const OnlyOneLang: Story = {
  render: () => (
    <Interactive
      label='IDP metadata XML'
      onlyOneLang
      language='xml'
      initialValue={'<EntityDescriptor entityID="https://example.com" />'}
    />
  ),
}
