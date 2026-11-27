import type { Meta, StoryObj } from 'storybook'

import { BodyText } from 'components/base/typography'

const meta: Meta<typeof BodyText> = {
  args: {
    children: 'Flags let you turn features on and off without deploying.',
  },
  component: BodyText,
  parameters: {
    docs: {
      description: {
        component:
          'Body text, a `<p>` by default and a `<span>` with `inline`. The default is 14px regular; `size` is `lg` (16px), `sm` (13px) or `xs` (12px) and `weight` is `semibold`. `muted` uses the secondary text colour. Other colours come from the `text-*` utilities.',
      },
    },
  },
  title: 'Components/Typography/BodyText',
}
export default meta

type Story = StoryObj<typeof BodyText>

export const Default: Story = {}

export const Large: Story = {
  args: { size: 'lg' },
}

export const Small: Story = {
  args: { size: 'sm' },
}

export const ExtraSmall: Story = {
  args: { size: 'xs' },
}

export const Semibold: Story = {
  args: { weight: 'semibold' },
}

export const Muted: Story = {
  args: { children: 'Last updated 2 days ago', muted: true, size: 'sm' },
}

export const Inline: Story = {
  render: () => (
    <BodyText>
      Serving to{' '}
      <BodyText inline weight='semibold'>
        Production
      </BodyText>{' '}
      <BodyText inline muted size='sm'>
        (2 days ago)
      </BodyText>
    </BodyText>
  ),
}
