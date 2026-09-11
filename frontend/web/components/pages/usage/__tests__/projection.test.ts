import { projectUsage } from 'components/pages/usage/projection'

// A 30 day period, with now sitting 15 days in.
const PERIOD = {
  ends_at: '2026-07-31T00:00:00Z',
  starts_at: '2026-07-01T00:00:00Z',
}

describe('projectUsage', () => {
  beforeEach(() => {
    jest.useFakeTimers().setSystemTime(new Date('2026-07-16T00:00:00Z'))
  })
  afterEach(() => {
    jest.useRealTimers()
  })

  it('doubles usage at the halfway point', () => {
    const projection = projectUsage(600_000, 2_000_000, PERIOD)

    expect(projection?.total).toBe(1_200_000)
    expect(projection?.percentOfLimit).toBe(60)
    expect(projection?.overLimit).toBe(false)
  })

  it('flags a projection that lands over the limit', () => {
    const projection = projectUsage(600_000, 1_000_000, PERIOD)

    expect(projection?.total).toBe(1_200_000)
    expect(projection?.percentOfLimit).toBe(120)
    expect(projection?.overLimit).toBe(true)
  })

  // Free plans have no period end to project to.
  it('says nothing on a rolling window', () => {
    expect(projectUsage(600_000, 50_000, null)).toBeUndefined()
  })

  it('says nothing before a fifth of the period has passed', () => {
    // Day 5 of 30 is a sixth.
    jest.setSystemTime(new Date('2026-07-06T00:00:00Z'))

    expect(projectUsage(100_000, 2_000_000, PERIOD)).toBeUndefined()
  })

  it('starts once a fifth has passed', () => {
    jest.setSystemTime(new Date('2026-07-07T00:00:00Z'))

    expect(projectUsage(100_000, 2_000_000, PERIOD)).toBeDefined()
  })

  // Without a plan limit there is a total but nothing to compare it against.
  it('projects a total with no limit to compare against', () => {
    const projection = projectUsage(600_000, null, PERIOD)

    expect(projection?.total).toBe(1_200_000)
    expect(projection?.percentOfLimit).toBeUndefined()
    expect(projection?.overLimit).toBe(false)
  })

  it('does not inflate past the end of the period', () => {
    jest.setSystemTime(new Date('2026-08-10T00:00:00Z'))

    // Elapsed is capped at the period, so the projection is the total itself.
    expect(projectUsage(900_000, 2_000_000, PERIOD)?.total).toBe(900_000)
  })
})
