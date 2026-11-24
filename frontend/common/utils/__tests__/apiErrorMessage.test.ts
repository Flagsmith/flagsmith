import { getApiErrorMessage } from 'common/utils/apiErrorMessage'

const FALLBACK = 'Failed to create experiment'
// What a proxy returns instead of a DRF body.
const HTML_BODY = '<!DOCTYPE html><html><body><h1>502</h1></body></html>'

describe('getApiErrorMessage', () => {
  it.each`
    body                                                                                       | expected
    ${['Audience segment 12 contains a percentage split']}                                     | ${'Audience segment 12 contains a percentage split'}
    ${{ non_field_errors: ['Audience segments must be unique'] }}                              | ${'Audience segments must be unique'}
    ${{ detail: 'Not found.' }}                                                                | ${'Not found.'}
    ${{ experiment_rollout: { audience: ['Bad audience'] } }}                                  | ${'Bad audience'}
    ${{ feature_states_to_update: [{ feature_state_value: { string_value: ['Too long'] } }] }} | ${'Too long'}
    ${HTML_BODY}                                                                               | ${FALLBACK}
    ${[]}                                                                                      | ${FALLBACK}
    ${{}}                                                                                      | ${FALLBACK}
    ${undefined}                                                                               | ${FALLBACK}
  `('returns $expected', ({ body, expected }) => {
    expect(getApiErrorMessage({ data: body }, FALLBACK)).toBe(expected)
  })

  it('falls back when there is no error body at all', () => {
    expect(getApiErrorMessage(undefined, FALLBACK)).toBe(FALLBACK)
  })
})
