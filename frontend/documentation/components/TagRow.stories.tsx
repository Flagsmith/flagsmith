import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'
import type { Tag } from 'common/types/responses'

import TagRow from 'components/tags/TagRow'
import DropdownMenu from 'components/base/DropdownMenu'

const tag = (over: Partial<Tag>): Tag => ({
  color: '#c7e6ff',
  description: '',
  id: 1,
  is_permanent: false,
  is_system_tag: false,
  label: 'billing',
  project: 1,
  type: 'NONE',
  ...over,
})

const meta: Meta<typeof TagRow> = {
  args: { tag: tag({}) },
  component: TagRow,
  parameters: {
    chromatic: { disableSnapshot: false },
    docs: {
      description: {
        component:
          'One tag in a list. Selection is marked on the row rather than inside the chip: a tag is a colour and a name, and whether it is currently picked is a fact about the row. Drawing it inside meant the chip fill ran behind a control that was not part of the tag. The mark is a trailing checkmark, matching every other list in the app: assignees, groups, roles and the table filters.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Tags/TagRow',
}
export default meta

type Story = StoryObj<typeof TagRow>

/** No mark: a row that shows a tag without offering to select it. */
export const ReadOnly: Story = { name: 'Not selectable' }

export const Unchecked: Story = {
  args: { checked: false, onToggle: () => undefined },
}

export const Checked: Story = {
  args: { checked: true, onToggle: () => undefined },
}

/** A stale tag on a plan without stale flags. Faded once, not twice. */
export const Disabled: Story = {
  args: {
    checked: false,
    disabled: true,
    onToggle: () => undefined,
    tag: tag({ label: 'Stale', type: 'STALE' }),
  },
}

export const WithUsage: Story = {
  args: { checked: false, onToggle: () => undefined, trailing: '3 features' },
  name: 'With a usage count',
}

export const WithMenu: Story = {
  args: {
    checked: false,
    onToggle: () => undefined,
    trailing: (
      <DropdownMenu
        items={[
          { icon: 'setting', label: 'Edit', onClick: () => undefined },
          { icon: 'trash-2', label: 'Delete', onClick: () => undefined },
        ]}
      />
    ),
  },
  name: 'With a menu',
}

/** Selection has to survive a click, which static args cannot show. */
const List: React.FC = () => {
  const [picked, setPicked] = useState<number[]>([1])
  const tags = [
    tag({ color: '#c7e6ff', id: 1, label: 'billing' }),
    tag({ color: '#c7e7e2', id: 2, label: 'analytics' }),
    tag({ color: '#d6f1d4', id: 3, label: 'onboarding' }),
    tag({ color: '#eff0f3', id: 4, label: 'archived' }),
  ]
  return (
    <div className='d-flex flex-column' style={{ maxWidth: 380 }}>
      {tags.map((t) => (
        <TagRow
          checked={picked.includes(t.id)}
          key={t.id}
          onToggle={() =>
            setPicked((p) =>
              p.includes(t.id) ? p.filter((id) => id !== t.id) : [...p, t.id],
            )
          }
          tag={t}
          trailing={`${t.id} features`}
        />
      ))}
    </div>
  )
}

export const AList: Story = {
  name: 'A list',
  render: () => <List />,
}
