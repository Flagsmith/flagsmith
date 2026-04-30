import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
import { useTabUrlSync } from 'common/hooks/useTabUrlSync'
import { withRouter } from './_decorators'

const meta: Meta = {
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

type Story = StoryObj

const DefaultRenderer = () => {
  const [tab, setTab] = useState(0)
  return (
    <Tabs value={tab} onChange={setTab}>
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
  )
}

export const Default: Story = {
  render: () => <DefaultRenderer />,
}

const PillThemeRenderer = () => {
  const [tab, setTab] = useState(0)
  return (
    <Tabs theme='pill' value={tab} onChange={setTab}>
      <TabItem tabLabel='Overview'>
        <p className='mt-3'>Overview content</p>
      </TabItem>
      <TabItem tabLabel='Activity'>
        <p className='mt-3'>Activity content</p>
      </TabItem>
    </Tabs>
  )
}

export const PillTheme: Story = {
  render: () => <PillThemeRenderer />,
}

const HideNavOnSingleTabRenderer = () => {
  const [tab, setTab] = useState(0)
  return (
    <Tabs hideNavOnSingleTab value={tab} onChange={setTab}>
      <TabItem tabLabel='Permissions'>
        <p className='mt-3'>
          Tab nav is hidden because there is only one TabItem.
        </p>
      </TabItem>
    </Tabs>
  )
}

export const HideNavOnSingleTab: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'Pass `hideNavOnSingleTab` so the tab bar collapses to nothing when only one TabItem is rendered (e.g. after permission or plan filtering removes the others). Avoids showing a single, useless tab button.',
      },
    },
  },
  render: () => <HideNavOnSingleTabRenderer />,
}

const URL_SYNC_LABELS = ['Overview', 'Activity', 'Settings']

const WithUrlSyncRenderer = () => {
  const [tab, setTab] = useTabUrlSync('demo', URL_SYNC_LABELS)
  return (
    <Tabs value={tab} onChange={setTab}>
      {URL_SYNC_LABELS.map((label) => (
        <TabItem key={label} tabLabel={label}>
          <p className='mt-3'>Active label: {label}.</p>
        </TabItem>
      ))}
    </Tabs>
  )
}

export const WithUrlSync: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'Compose `useTabUrlSync(paramName, labels)` with a controlled `<Tabs value onChange>` to persist the active tab in a URL query param. Labels are slugified (lowercase, spaces → hyphens). The hook also handles modal-portal contexts where `useHistory()` is unavailable by falling back to `history.replaceState`.',
      },
    },
  },
  render: () => <WithUrlSyncRenderer />,
}

const ControlledRenderer = () => {
  const [tab, setTab] = useState(0)
  return (
    <Tabs value={tab} onChange={setTab}>
      <TabItem tabLabel='Overview'>
        <p className='mt-3'>Active index: {tab}</p>
      </TabItem>
      <TabItem tabLabel='Activity'>
        <p className='mt-3'>Active index: {tab}</p>
      </TabItem>
    </Tabs>
  )
}

export const Controlled: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'Tabs is controlled — pass `value` (active index) and `onChange`. For local state use `useState`, for URL state use `useTabUrlSync`. Avoid the legacy `uncontrolled` and `urlParam` props on new code.',
      },
    },
  },
  render: () => <ControlledRenderer />,
}

const WithDirtyMarkerRenderer = () => {
  const [tab, setTab] = useState(0)
  return (
    <Tabs value={tab} onChange={setTab}>
      <TabItem tabLabel='Value' isDirty>
        <p className='mt-3'>This tab has unsaved changes.</p>
      </TabItem>
      <TabItem tabLabel='Segment Overrides' isDirty>
        <p className='mt-3'>This tab also has unsaved changes.</p>
      </TabItem>
      <TabItem tabLabel='Settings'>
        <p className='mt-3'>No unsaved changes here.</p>
      </TabItem>
    </Tabs>
  )
}

export const WithDirtyMarker: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'Set `isDirty` on a `TabItem` to show an unsaved-changes badge next to its label. The badge sits inside an inline-flex wrapper so it never breaks onto a second line and stays vertically aligned with the label.',
      },
    },
  },
  render: () => <WithDirtyMarkerRenderer />,
}
