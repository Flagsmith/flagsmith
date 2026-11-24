import { getSaveFeedback } from 'components/modals/create-feature/saveFeedback'

const FALLBACK = 'Could not save this feature. Please try again.'
const tooLong = {
  data: {
    feature_states_to_update: [
      { feature_state_value: { string_value: ['Too long'] } },
    ],
  },
  status: 400,
}

describe('getSaveFeedback', () => {
  it.each`
    error                                                                       | expected
    ${undefined}                                                                | ${''}
    ${'Something broke'}                                                        | ${'Something broke'}
    ${new Error('Feature contains no changes')}                                 | ${'Feature contains no changes'}
    ${{ message: 'Feature contains no changes', name: 'Error', stack: 'at x' }} | ${'Feature contains no changes'}
    ${tooLong}                                                                  | ${'Too long'}
    ${{ name: ['Name already exists'] }}                                        | ${'Name already exists'}
    ${{ data: '<html>502</html>' }}                                             | ${FALLBACK}
  `('returns "$expected" for $error', ({ error, expected }) => {
    expect(getSaveFeedback(error, false)).toEqual({
      error: expected,
      warning: '',
    })
  })

  it('turns "no changes" into a warning when the feature has variations', () => {
    const result = getSaveFeedback(
      new Error('Feature contains no changes'),
      true,
    )
    expect(result.error).toBe('')
    expect(result.warning).toContain('no changes')
  })
})
