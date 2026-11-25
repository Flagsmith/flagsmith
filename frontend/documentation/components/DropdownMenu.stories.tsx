import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'
import { screen, userEvent, within } from 'storybook/test'

import DropdownMenu, { DropdownMenuItem } from 'components/base/DropdownMenu'
import Button from 'components/base/forms/Button'

const meta: Meta<typeof DropdownMenu> = {
  component: DropdownMenu,
  parameters: {
    docs: { story: { height: '320px' } },
    layout: 'centered',
  },
  title: 'Components/Data Display/DropdownMenu',
}
export default meta

type Story = StoryObj<typeof DropdownMenu>

const noop = () => undefined

const ActionsMenu = () => (
  <DropdownMenu aria-label='Feature actions'>
    <DropdownMenuItem icon='copy' onSelect={noop}>
      Copy feature name
    </DropdownMenuItem>
    <DropdownMenuItem icon='list' onSelect={noop}>
      Show audit logs
    </DropdownMenuItem>
    <DropdownMenuItem
      icon='clock'
      disabled
      disabledReason='History needs feature versioning'
      onSelect={noop}
    >
      Show history
    </DropdownMenuItem>
    <DropdownMenuItem icon='trash-2' destructive onSelect={noop}>
      Remove feature
    </DropdownMenuItem>
  </DropdownMenu>
)

const SECTIONS = ['Value', 'Segment overrides', 'History', 'Settings']

const SectionsMenu = () => {
  const [current, setCurrent] = useState(2)
  return (
    <DropdownMenu
      aria-label='Sections'
      trigger={<Button theme='secondary'>{SECTIONS[current]}</Button>}
    >
      {SECTIONS.map((section, i) => (
        <DropdownMenuItem
          key={section}
          current={current === i}
          onSelect={() => setCurrent(i)}
        >
          {section}
        </DropdownMenuItem>
      ))}
    </DropdownMenu>
  )
}

const openMenu = async (canvasElement: HTMLElement, name: string) => {
  const canvas = within(canvasElement)
  await userEvent.click(canvas.getByRole('button', { name }))
  await screen.findByRole('dialog')
}

export const Actions: Story = {
  parameters: { chromatic: { delay: 300 } },
  play: ({ canvasElement }: { canvasElement: HTMLElement }) =>
    openMenu(canvasElement, 'Feature actions'),
  render: () => <ActionsMenu />,
}

export const CurrentItem: Story = {
  parameters: { chromatic: { delay: 300 } },
  play: ({ canvasElement }: { canvasElement: HTMLElement }) =>
    openMenu(canvasElement, 'History'),
  render: () => <SectionsMenu />,
}

// On phones the menu opens as a bottom sheet
export const MobileSheet: Story = {
  globals: { viewport: { isRotated: false, value: 'mobile1' } },
  parameters: {
    chromatic: { delay: 300 },
    docs: { story: { height: '420px', inline: false } },
  },
  play: ({ canvasElement }: { canvasElement: HTMLElement }) =>
    openMenu(canvasElement, 'Feature actions'),
  render: () => <ActionsMenu />,
}
