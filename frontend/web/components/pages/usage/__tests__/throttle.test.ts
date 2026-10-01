import { isThrottled } from 'components/pages/usage/throttle'

describe('isThrottled', () => {
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
})
