import React from 'react'
import type { Meta, StoryObj } from 'storybook'

import Paging from 'components/Paging'
import Panel from 'components/base/grid/Panel'

const meta: Meta = {
  parameters: {
    chromatic: { disableSnapshot: false },
    docs: {
      description: {
        component:
          'Pagination controls used by paginated lists (identities, audit log, change requests, etc.). Renders previous/next arrows, the page numbers around the current page, and the "x-y of n" summary.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Patterns/Paging',
}
export default meta

type Story = StoryObj

const noop = () => undefined

const paging = {
  count: 45,
  currentPage: 3,
  next: 'next',
  pageSize: 10,
  previous: 'previous',
}

export const Default: Story = {
  render: () => (
    <Paging goToPage={noop} nextPage={noop} paging={paging} prevPage={noop} />
  ),
}

export const InsidePanel: Story = {
  parameters: {
    docs: {
      description: {
        story:
          'Paging as rendered at the bottom of a list panel, e.g. the identities tab. Switch the toolbar theme to dark to check the arrows stay visible.',
      },
    },
  },
  render: () => (
    <Panel title='Identities'>
      <p className='mb-0'>List content</p>
      <Paging goToPage={noop} nextPage={noop} paging={paging} prevPage={noop} />
    </Panel>
  ),
}

export const FirstPage: Story = {
  parameters: {
    docs: {
      description: {
        story: 'On the first page the previous arrow is disabled.',
      },
    },
  },
  render: () => (
    <Panel title='Identities'>
      <p className='mb-0'>List content</p>
      <Paging
        goToPage={noop}
        nextPage={noop}
        paging={{ ...paging, currentPage: 1, previous: null }}
        prevPage={noop}
      />
    </Panel>
  ),
}

export const Loading: Story = {
  render: () => (
    <Panel title='Identities'>
      <p className='mb-0'>List content</p>
      <Paging
        goToPage={noop}
        isLoading
        nextPage={noop}
        paging={paging}
        prevPage={noop}
      />
    </Panel>
  ),
}
