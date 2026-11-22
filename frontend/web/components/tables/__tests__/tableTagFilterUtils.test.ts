import { matchesTagFilter } from 'components/tables/tableTagFilterUtils'

describe('matchesTagFilter', () => {
  it.each([
    ['Onboarding', 'onboard', true],
    ['Onboarding', 'ONBOARD', true],
    ['ΟΣ', 'οσ', true],
    ['archived', 'ARCH', true],
    ['untagged', 'TAG', true],
    ['Onboarding', 'release', false],
  ])('matches "%s" against "%s" as %s', (label, filter, expected) => {
    // Given
    const tagLabel = label

    // When
    const result = matchesTagFilter(tagLabel, filter)

    // Then
    expect(result).toBe(expected)
  })
})
