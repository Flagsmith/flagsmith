import { isNumericId } from 'common/utils/isNumericId'

describe('isNumericId', () => {
  it.each([1, 42, '7'])('accepts %p', (id) => {
    expect(isNumericId(id)).toBe(true)
  })

  // 'account' prompted this: it reached projects/?organisation=account, which
  // the API rejects as not an integer.
  it.each(['account', 'undefined', 'NaN', '1.5', 'getting-started'])(
    'refuses %p',
    (id) => {
      expect(isNumericId(id)).toBe(false)
    },
  )

  it.each([undefined, null, '', 0, NaN])('refuses %p', (id) => {
    expect(isNumericId(id)).toBe(false)
  })

  // Number() turns each of these into an integer, so truthiness alone lets
  // them through.
  it.each([true, [], ['5'], {}])('refuses the coercible %p', (id) => {
    expect(isNumericId(id)).toBe(false)
  })

  // 0 and '0' disagreed under the truthiness check. Neither is a primary key.
  it.each(['0', 0, '-1', -1])(
    'refuses %p, which is not a primary key',
    (id) => {
      expect(isNumericId(id)).toBe(false)
    },
  )
})
