import {
  matchesSearch,
  searchTerm,
  showsRow,
} from 'components/tables/tagFilterSearch'

describe('searchTerm', () => {
  it.each([
    ['Onboarding', 'onboarding'],
    ['  blue  ', 'blue'],
    ['', ''],
  ])('reduces %s to %s', (input, expected) => {
    expect(searchTerm(input)).toBe(expected)
  })
})

describe('matchesSearch', () => {
  // The bug: a tag shown as "Onboarding" was only found by typing it lower.
  it('matches a label by the capital it displays with', () => {
    expect(matchesSearch('Onboarding', 'Onboarding')).toBe(true)
  })

  // Reducing twice is the same as reducing once, so a caller may pass either.
  it('takes a raw term or a reduced one', () => {
    expect(matchesSearch('Onboarding', '  BOARD  ')).toBe(true)
    expect(matchesSearch('Onboarding', searchTerm('  BOARD  '))).toBe(true)
  })

  it.each([
    ['Onboarding', 'onboarding', true],
    ['Onboarding', 'board', true],
    ['Onboarding', 'ONBOARD', true],
    ['Onboarding', 'zzz', false],
    ['Onboarding', '', true],
  ])('%s against %s is %s', (label, search, expected) => {
    expect(matchesSearch(label, search)).toBe(expected)
  })
})

describe('showsRow', () => {
  it('shows a row that matches', () => {
    expect(
      showsRow({ isActive: false, label: 'archived', search: 'arch' }),
    ).toBe(true)
  })

  it('hides a row that does not', () => {
    expect(
      showsRow({ isActive: false, label: 'archived', search: 'zzz' }),
    ).toBe(false)
  })

  // Hiding it would leave a filter applied with nothing to switch off.
  it('keeps an active row whatever is typed', () => {
    expect(showsRow({ isActive: true, label: 'archived', search: 'zzz' })).toBe(
      true,
    )
  })
})
