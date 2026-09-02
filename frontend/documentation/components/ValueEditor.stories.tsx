import React, { useEffect, useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import Constants from 'common/constants'
import ValueEditor from 'components/ValueEditor'
import ControlWeightChip from 'components/mv/ControlWeightChip'

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
      <ValueEditor
        data-test='valueEditor'
        {...props}
        value={value}
        onChange={setValue}
      />
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

// A value that arrives after mount, the way a loaded feature does. Detection
// has to wait for it: a mount-only check left JSON rendering as .txt.
const LateLoading = () => {
  const [value, setValue] = useState<string>('')
  useEffect(() => {
    const timer = setTimeout(() => setValue('{ "colour": "blue" }'), 150)
    return () => clearTimeout(timer)
  }, [])
  return (
    <div style={{ maxWidth: 640, padding: 16 }}>
      <ValueEditor label='Value' value={value} onChange={setValue} />
    </div>
  )
}

export const ValueArrivesAfterMount: Story = {
  render: () => <LateLoading />,
}

// Invalid JSON surfaces a warning against the active language label.
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

// The multivariate control value carries a weight chip and a tooltip, so it is
// the widest label this component gets. Label and format buttons share one flex
// row, so they compress rather than overlap.
const controlWeight = <ControlWeightChip percentage={100} />

export const BadgeLabel: Story = {
  render: () => (
    <Interactive
      label='Control Value'
      labelAfter={controlWeight}
      labelTooltip={Constants.strings.REMOTE_CONFIG_DESCRIPTION_VARIATION}
      initialValue='DEFAULT_VALUE'
    />
  ),
}

// The same label at the narrowest width the drawer reaches.
export const BadgeLabelNarrow: Story = {
  render: () => (
    <Interactive
      label='Control Value'
      labelAfter={controlWeight}
      labelTooltip={Constants.strings.REMOTE_CONFIG_DESCRIPTION_VARIATION}
      initialValue='DEFAULT_VALUE'
      width={380}
    />
  ),
}
