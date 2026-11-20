import type { Meta, StoryObj } from 'storybook'

import HeadingText from 'components/base/HeadingText'

const meta: Meta<typeof HeadingText> = {
  args: { children: 'Feature flags', level: 1 },
  component: HeadingText,
  parameters: {
    docs: {
      description: {
        component:
          'A heading. `level` sets the tag and, by default, the size: 1 is 24px, 2 is 18px, 3 to 6 are 16px. Pick the level from the page structure. `size` (`lg`, `md`, `sm`) overrides the size only when the design needs it.',
      },
    },
  },
  title: 'Components/Typography/HeadingText',
}
export default meta

type Story = StoryObj<typeof HeadingText>

export const Level1: Story = {}

export const Level2: Story = {
  args: { children: 'Environments', level: 2 },
}

export const Level3: Story = {
  args: { children: 'Segment overrides', level: 3 },
}

export const Level1Small: Story = {
  args: { children: 'Settings', level: 1, size: 'sm' },
}

export const AllLevels: Story = {
  render: () => (
    <div className='d-flex flex-column gap-2'>
      <HeadingText level={1}>Level 1</HeadingText>
      <HeadingText level={2}>Level 2</HeadingText>
      <HeadingText level={3}>Level 3</HeadingText>
      <HeadingText level={4}>Level 4</HeadingText>
      <HeadingText level={5}>Level 5</HeadingText>
      <HeadingText level={6}>Level 6</HeadingText>
    </div>
  ),
}
