import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
import { withRouter } from './_decorators'

const DIRTY_MARKER_TABS = ['Value', 'Segment Overrides', 'Settings'] as const
type DirtyMarkerTab = (typeof DIRTY_MARKER_TABS)[number]

type DirtyMarkerArgs = {
  theme: 'tab' | 'pill'
  dirtyTabs: DirtyMarkerTab[]
}

const meta: Meta<DirtyMarkerArgs> = {
  argTypes: {
    dirtyTabs: {
      control: 'check',
      description: 'Which tabs show the unsaved-changes badge.',
      options: DIRTY_MARKER_TABS,
    },
    theme: {
      control: 'radio',
      description: 'Visual variant of the tab bar.',
      options: ['tab', 'pill'],
    },
  },
  decorators: [withRouter],
  parameters: {
    docs: {
      description: {
        component:
          'In-page tabs for splitting content into sections (e.g. Settings ▸ General | Permissions | Webhooks). Compose with `TabItem` children. Use the default theme for primary navigation between content areas; use `theme="pill"` for compact secondary switching.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Navigation/Tabs',
}
export default meta

type Story = StoryObj<DirtyMarkerArgs>

export const Default: Story = {
  render: () => (
    <Tabs uncontrolled>
      <TabItem tabLabel='Features'>
        <p className='mt-3'>Features tab content</p>
      </TabItem>
      <TabItem tabLabel='Segments'>
        <p className='mt-3'>Segments tab content</p>
      </TabItem>
      <TabItem tabLabel='Settings'>
        <p className='mt-3'>Settings tab content</p>
      </TabItem>
    </Tabs>
  ),
}

export const PillTheme: Story = {
  render: () => (
    <Tabs theme='pill' uncontrolled>
      <TabItem tabLabel='Overview'>
        <p className='mt-3'>Overview content</p>
      </TabItem>
      <TabItem tabLabel='Activity'>
        <p className='mt-3'>Activity content</p>
      </TabItem>
    </Tabs>
  ),
}

export const WithDirtyMarker: Story = {
  args: {
    dirtyTabs: ['Value', 'Segment Overrides'],
    theme: 'tab',
  },
  parameters: {
    docs: {
      description: {
        story:
          'Set `isDirty` on a `TabItem` to surface an unsaved-changes indicator on its label. Use the controls to toggle dirty state per tab and switch between the default and pill themes.',
      },
    },
  },
  render: ({ dirtyTabs, theme }) => (
    <Tabs theme={theme} uncontrolled>
      {DIRTY_MARKER_TABS.map((label) => (
        <TabItem
          key={label}
          tabLabel={label}
          isDirty={dirtyTabs.includes(label)}
        >
          <p className='mt-3'>
            {dirtyTabs.includes(label)
              ? 'This tab has unsaved changes.'
              : 'No unsaved changes here.'}
          </p>
        </TabItem>
      ))}
    </Tabs>
  ),
}

export const WithDirtyMarkerOnPillTheme: Story = {
  ...WithDirtyMarker,
  args: {
    dirtyTabs: ['Value', 'Segment Overrides'],
    theme: 'pill',
  },
  parameters: {
    docs: {
      description: {
        story:
          'The same `isDirty` pattern as the default theme, in the pill variant.',
      },
    },
  },
}
