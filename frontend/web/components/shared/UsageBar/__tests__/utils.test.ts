import {
  boundPercent,
  toneFor,
  usagePercent,
} from 'components/shared/UsageBar/utils'

describe('UsageBar utils', () => {
  describe('usagePercent', () => {
    it.each`
      usage  | limit        | expected
      ${0}   | ${100}       | ${0}
      ${50}  | ${100}       | ${50}
      ${118} | ${100}       | ${118}
      ${1}   | ${3}         | ${33}
      ${2}   | ${3}         | ${67}
      ${10}  | ${0}         | ${0}
      ${10}  | ${null}      | ${0}
      ${10}  | ${undefined} | ${0}
      ${10}  | ${-5}        | ${0}
    `('$usage of $limit is $expected%', ({ expected, limit, usage }) => {
      expect(usagePercent(usage, limit)).toBe(expected)
    })
  })

  describe('boundPercent', () => {
    it.each`
      percent | expected
      ${-10}  | ${0}
      ${0}    | ${0}
      ${55}   | ${55}
      ${100}  | ${100}
      ${118}  | ${100}
    `('clamps $percent to $expected', ({ expected, percent }) => {
      expect(boundPercent(percent)).toBe(expected)
    })
  })

  describe('toneFor', () => {
    it.each`
      percent | warnAt | expected
      ${0}    | ${85}  | ${'success'}
      ${84}   | ${85}  | ${'success'}
      ${85}   | ${85}  | ${'warning'}
      ${99}   | ${85}  | ${'warning'}
      ${100}  | ${85}  | ${'danger'}
      ${250}  | ${85}  | ${'danger'}
      ${74}   | ${75}  | ${'success'}
      ${75}   | ${75}  | ${'warning'}
    `(
      '$percent% against a $warnAt% threshold is $expected',
      ({ expected, percent, warnAt }) => {
        expect(toneFor(percent, warnAt)).toBe(expected)
      },
    )
  })
})
