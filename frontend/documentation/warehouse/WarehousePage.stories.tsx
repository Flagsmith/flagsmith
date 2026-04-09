import type { Meta, StoryObj } from 'storybook'
import WarehousePage from 'components/warehouse/WarehousePage'

const meta: Meta<typeof WarehousePage> = {
  component: WarehousePage,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
  title: 'Warehouse/WarehousePage',
}
export default meta

type Story = StoryObj<typeof WarehousePage>

export const Empty: Story = {
  args: { initialState: 'empty' },
}

export const Configuring: Story = {
  args: { initialState: 'configuring' },
}

export const Testing: Story = {
  args: { initialState: 'testing' },
}

export const Connected: Story = {
  args: { initialState: 'connected' },
}

export const Error: Story = {
  args: { initialState: 'error' },
}
