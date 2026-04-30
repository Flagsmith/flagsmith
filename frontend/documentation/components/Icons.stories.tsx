import React, { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'
import Icon from 'components/icons/Icon'
import type { IconName } from 'components/icons/Icon'

// eslint-disable-next-line @dword-design/import-alias/prefer-alias
import '../docs.scss'

const meta: Meta = {
  parameters: { layout: 'padded' },
  title: 'Components/Icons',
}
export default meta

type IconCategory = {
  label: string
  icons: IconName[]
}

const CATEGORIES: IconCategory[] = [
  {
    icons: [
      'arrow-left',
      'arrow-right',
      'chevron-down',
      'chevron-left',
      'chevron-right',
      'chevron-up',
      'expand',
      'link',
      'open-external-link',
    ],
    label: 'Navigation',
  },
  {
    icons: [
      'close',
      'close-circle',
      'copy',
      'copy-outlined',
      'edit',
      'minus-circle',
      'more-vertical',
      'options-2',
      'plus',
      'refresh',
      'search',
      'trash-2',
    ],
    label: 'Actions',
  },
  {
    icons: [
      'checkmark',
      'checkmark-circle',
      'checkmark-square',
      'eye',
      'eye-off',
      'info',
      'info-outlined',
      'lock',
      'shield',
      'warning',
    ],
    label: 'Status',
  },
  {
    icons: [
      'github',
      'issue-closed',
      'issue-linked',
      'pr-closed',
      'pr-draft',
      'pr-linked',
      'pr-merged',
    ],
    label: 'GitHub',
  },
  {
    icons: [
      'bar-chart',
      'features',
      'flash',
      'flask',
      'layers',
      'list',
      'pie-chart',
      'rocket',
      'setting',
    ],
    label: 'Features',
  },
  {
    icons: ['people', 'person'],
    label: 'People',
  },
  {
    icons: ['code', 'file-text', 'height', 'radio', 'request'],
    label: 'Content',
  },
  {
    icons: ['bell', 'calendar', 'clock', 'timer'],
    label: 'Time',
  },
  {
    icons: ['moon', 'sun'],
    label: 'Theme',
  },
  {
    icons: ['award', 'google'],
    label: 'Brand',
  },
]

const ALL_ICONS = CATEGORIES.flatMap((c) => c.icons)

const IconCard: React.FC<{ name: IconName }> = ({ name }) => (
  <div className='icon-catalogue__card'>
    <Icon name={name} width={24} fill='currentColor' />
    <code>{name}</code>
  </div>
)

const IconCatalogue: React.FC = () => {
  const [search, setSearch] = useState('')
  const query = search.toLowerCase()

  return (
    <div>
      <h2 className='icon-catalogue__header'>Icon Catalogue</h2>
      <p className='icon-catalogue__description'>
        {ALL_ICONS.length} icons from <code>{'<Icon />'}</code>. Use:{' '}
        <code>{'<Icon name="checkmark" />'}</code>
      </p>
      <input
        className='icon-catalogue__search'
        onChange={(e) => setSearch(e.target.value)}
        placeholder='Search icons...'
        type='text'
        value={search}
      />
      {CATEGORIES.map(({ icons, label }) => {
        const filtered = icons.filter((name) =>
          name.toLowerCase().includes(query),
        )
        if (filtered.length === 0) return null
        return (
          <div className='icon-catalogue__category' key={label}>
            <h3 className='icon-catalogue__category-label'>{label}</h3>
            <div className='icon-catalogue__grid'>
              {filtered.map((name) => (
                <IconCard key={name} name={name} />
              ))}
            </div>
          </div>
        )
      })}
      {ALL_ICONS.filter((n) => n.includes(query)).length === 0 && (
        <p className='icon-catalogue__empty'>
          No icons match &ldquo;{search}&rdquo;
        </p>
      )}
    </div>
  )
}

export const Catalogue: StoryObj = {
  name: 'All icons',
  render: () => <IconCatalogue />,
}
