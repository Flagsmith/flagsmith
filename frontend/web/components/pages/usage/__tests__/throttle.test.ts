import { isThrottled, throttledMessage } from 'components/pages/usage/throttle'

describe('throttle', () => {
  it.each`
    error                        | expected
    ${{ status: 429 }}           | ${true}
    ${{ status: 500 }}           | ${false}
    ${{ status: 'FETCH_ERROR' }} | ${false}
    ${undefined}                 | ${false}
    ${null}                      | ${false}
  `('$error is throttled: $expected', ({ error, expected }) => {
    expect(isThrottled(error)).toBe(expected)
  })

  it('says when it retries', () => {
    expect(throttledMessage(42)).toBe(
      'Usage is limited to a few requests a minute. Retrying in 42s.',
    )
  })
})
