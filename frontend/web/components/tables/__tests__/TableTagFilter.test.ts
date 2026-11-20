import {
  isSpecialFilterItemVisible,
  isTagMatchingFilter,
} from 'components/tables/TableTagFilter'

describe('TableTagFilter helpers', () => {
  describe('isTagMatchingFilter', () => {
    it('returns true when filter is empty or only whitespace', () => {
      expect(isTagMatchingFilter('Onboarding', '')).toBe(true)
      expect(isTagMatchingFilter('Onboarding', '   ')).toBe(true)
    })

    it('matches tag case-insensitively when user enters lower, upper, or mixed case', () => {
      expect(isTagMatchingFilter('Onboarding', 'onboarding')).toBe(true)
      expect(isTagMatchingFilter('Onboarding', 'ONBOARDING')).toBe(true)
      expect(isTagMatchingFilter('Onboarding', 'Onboarding')).toBe(true)
      expect(isTagMatchingFilter('Onboarding', 'oNbOaRdInG')).toBe(true)
    })

    it('matches partial tag labels case-insensitively', () => {
      expect(isTagMatchingFilter('Onboarding', 'board')).toBe(true)
      expect(isTagMatchingFilter('Onboarding', 'BOARD')).toBe(true)
      expect(isTagMatchingFilter('Onboarding', 'onb')).toBe(true)
    })

    it('returns false when tag label does not contain the filter', () => {
      expect(isTagMatchingFilter('Onboarding', 'billing')).toBe(false)
      expect(isTagMatchingFilter('Release 2.0', 'onb')).toBe(false)
    })
  })

  describe('isSpecialFilterItemVisible', () => {
    it('returns true when filter is empty or whitespace', () => {
      expect(isSpecialFilterItemVisible('archived', '')).toBe(true)
      expect(isSpecialFilterItemVisible('untagged', '')).toBe(true)
      expect(isSpecialFilterItemVisible('archived', '   ')).toBe(true)
      expect(isSpecialFilterItemVisible('untagged', '   ')).toBe(true)
    })

    it('matches archived case-insensitively', () => {
      expect(isSpecialFilterItemVisible('archived', 'archived')).toBe(true)
      expect(isSpecialFilterItemVisible('archived', 'ARCHIVED')).toBe(true)
      expect(isSpecialFilterItemVisible('archived', 'Arch')).toBe(true)
      expect(isSpecialFilterItemVisible('archived', 'arch')).toBe(true)
    })

    it('matches untagged case-insensitively', () => {
      expect(isSpecialFilterItemVisible('untagged', 'untagged')).toBe(true)
      expect(isSpecialFilterItemVisible('untagged', 'UNTAGGED')).toBe(true)
      expect(isSpecialFilterItemVisible('untagged', 'Untag')).toBe(true)
      expect(isSpecialFilterItemVisible('untagged', 'tag')).toBe(true)
    })

    it('hides archived and untagged when search filter does not match them', () => {
      expect(isSpecialFilterItemVisible('archived', 'onboarding')).toBe(false)
      expect(isSpecialFilterItemVisible('untagged', 'onboarding')).toBe(false)
      expect(isSpecialFilterItemVisible('archived', 'production')).toBe(false)
      expect(isSpecialFilterItemVisible('untagged', 'staging')).toBe(false)
    })
  })
})
