import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import Constants from 'common/constants'
import ValueEditor from 'components/ValueEditor'

const meta: Meta = {
  parameters: { chromatic: { disableSnapshot: false } },
  title: 'Components/Forms/ValueEditor',
}
export default meta

type Story = StoryObj

const Interactive = ({
  initialValue = '',
  width = 640,
  ...props
}: Record<string, any>) => {
  const [value, setValue] = useState(initialValue)
  return (
    <div style={{ maxWidth: width, padding: 16 }}>
      <ValueEditor {...props} value={value} onChange={setValue} />
    </div>
  )
}

// Empty state. The "Enter a value..." text is not a real ::placeholder — it is
// rendered into the contenteditable and styled by `code.txt.empty`.
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
      labelTooltip={Constants.strings.REMOTE_CONFIG_DESCRIPTION_VARIATION}
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

// The multivariate control value carries a weight chip and a tooltip, so it is
// the widest label this component gets. Label and format buttons share one flex
// row, so they compress rather than overlap.
const ControlValueLabel = (
  <span className='d-inline-flex align-items-center'>
    Control Value
    <span className='chip chip--xs ml-2'>100%</span>
  </span>
)

export const BadgeLabel: Story = {
  render: () => (
    <Interactive
      label={ControlValueLabel}
      labelTooltip={Constants.strings.REMOTE_CONFIG_DESCRIPTION_VARIATION}
      initialValue='DEFAULT_VALUE'
    />
  ),
}

// The same label at the narrowest width the drawer reaches.
export const BadgeLabelNarrow: Story = {
  render: () => (
    <Interactive
      label={ControlValueLabel}
      labelTooltip={Constants.strings.REMOTE_CONFIG_DESCRIPTION_VARIATION}
      initialValue='DEFAULT_VALUE'
      width={380}
    />
  ),
}
