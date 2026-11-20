import { readOnboardingStatus } from 'components/pages/onboarding/hooks/readOnboardingStatus'

const MOUNTED_AT = 1000
const notEvaluated = {
  first_evaluated_at: null,
  first_evaluated_sdk_label: null,
}
const evaluated = {
  first_evaluated_at: '2026-11-19T10:00:00Z',
  first_evaluated_sdk_label: 'flagsmith-js-sdk',
}

describe('readOnboardingStatus', () => {
  it.each`
    data            | fetchedAt    | expected
    ${undefined}    | ${undefined} | ${'unknown'}
    ${notEvaluated} | ${2000}      | ${'listening'}
    ${notEvaluated} | ${500}       | ${'unknown'}
    ${notEvaluated} | ${undefined} | ${'unknown'}
    ${evaluated}    | ${500}       | ${'connected'}
    ${evaluated}    | ${2000}      | ${'connected'}
  `(
    'reads $expected when fetched at $fetchedAt',
    ({ data, expected, fetchedAt }) => {
      expect(readOnboardingStatus(data, fetchedAt, MOUNTED_AT)).toBe(expected)
    },
  )
})
