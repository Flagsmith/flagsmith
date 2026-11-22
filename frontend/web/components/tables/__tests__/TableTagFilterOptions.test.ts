import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { Tag } from 'common/types/responses'
import TableTagFilterOptions from 'components/tables/TableTagFilterOptions'

jest.mock('../TableFilterItem', () => ({
  __esModule: true,
  default: ({ title }: { title: React.ReactNode }) =>
    React.createElement('div', null, title),
}))

jest.mock('components/tags/Tag', () => ({
  __esModule: true,
  default: () => null,
}))

jest.mock('components/tags/TagContent', () => ({
  __esModule: true,
  default: ({ tag }: { tag: Tag }) =>
    React.createElement('span', null, tag.label),
}))

jest.mock('common/utils/utils', () => ({
  __esModule: true,
  default: { tagDisabled: () => false },
}))

const tag: Tag = {
  color: '',
  description: '',
  id: 1,
  is_permanent: false,
  is_system_tag: false,
  label: 'Onboarding',
  project: 1,
  type: 'NONE',
}

const renderOptions = (filter: string) =>
  renderToStaticMarkup(
    React.createElement(TableTagFilterOptions, {
      filter,
      isLoading: false,
      onChange: jest.fn(),
      onToggleArchived: jest.fn(),
      showArchived: false,
      tags: [tag],
      value: [],
    }),
  )

describe('TableTagFilterOptions', () => {
  it('renders a matching special option without unrelated options', () => {
    // Given
    const filter = 'ARCH'

    // When
    const markup = renderOptions(filter)

    // Then
    expect(markup).toContain('archived')
    expect(markup).not.toContain('untagged')
    expect(markup).not.toContain('Onboarding')
    expect(markup).not.toContain('No tags')
  })

  it('renders normal tags case-insensitively and hides special options', () => {
    // Given
    const filter = 'ONBOARD'

    // When
    const markup = renderOptions(filter)

    // Then
    expect(markup).toContain('Onboarding')
    expect(markup).not.toContain('archived')
    expect(markup).not.toContain('untagged')
    expect(markup).not.toContain('No tags')
  })

  it('renders the empty state when no option matches', () => {
    // Given
    const filter = 'missing'

    // When
    const markup = renderOptions(filter)

    // Then
    expect(markup).toContain('No tags')
    expect(markup).not.toContain('archived')
    expect(markup).not.toContain('untagged')
  })
})
