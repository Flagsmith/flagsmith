import { formatCountdown } from 'common/hooks/useCountdown'

describe('formatCountdown', () => {
  it('renders seconds only under a minute', () => {
    expect(formatCountdown(0)).toBe('0s')
    expect(formatCountdown(45)).toBe('45s')
  })

  it('renders minutes and seconds at or above a minute', () => {
    expect(formatCountdown(60)).toBe('1m 0s')
    expect(formatCountdown(90)).toBe('1m 30s')
    expect(formatCountdown(305)).toBe('5m 5s')
  })
})
