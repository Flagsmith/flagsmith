import { projectionNote, projectUsage } from 'components/pages/usage/projection'

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

  describe('when the usage data lags the clock', () => {
    // Measured through 10 July is ten days of a thirty day period, so the
    // rate is a third of what the clock's fifteen days would have given.
    it('divides by the days the total covers, not the days elapsed', () => {
      expect(projectUsage(600_000, null, PERIOD, '2026-07-10')?.total).toBe(
        1_800_000,
      )
    })

    it('counts the last measured day as complete', () => {
      // Measured through 15 July is exactly half the period, matching the
      // clock at midnight on the 16th.
      expect(projectUsage(600_000, null, PERIOD, '2026-07-15')?.total).toBe(
        1_200_000,
      )
    })

    it('falls back to the clock without a measured day', () => {
      expect(projectUsage(600_000, null, PERIOD)?.total).toBe(1_200_000)
    })

    it('ignores a measured day outside the period', () => {
      expect(projectUsage(600_000, null, PERIOD, '2026-06-20')?.total).toBe(
        1_200_000,
      )
    })

    it('ignores an unparseable measured day', () => {
      expect(projectUsage(600_000, null, PERIOD, '2026-13-45')?.total).toBe(
        1_200_000,
      )
    })

    // Two days of data cannot carry a projection, however far the clock has
    // run past them.
    it('withholds a projection while the data covers too little', () => {
      jest.setSystemTime(new Date('2026-07-20T00:00:00Z'))

      expect(
        projectUsage(100_000, 2_000_000, PERIOD, '2026-07-02'),
      ).toBeUndefined()
    })
  })
})

describe('projectionNote', () => {
  it('names the landing total, its share and the period end', () => {
    expect(
      projectionNote(
        { overLimit: false, percentOfLimit: 94, total: 1900000 },
        '2026-08-17T00:00:00Z',
      ),
      // The end is exclusive, so the sentence names 16 August.
    ).toBe('Estimated to reach ~1.9M (94% of your limit) by 16 Aug.')
  })

  it('says so when the line lands over the limit', () => {
    expect(
      projectionNote(
        { overLimit: true, percentOfLimit: 135, total: 2700000 },
        '2026-10-08T00:00:00Z',
      ),
    ).toContain('That lands over your limit.')
  })

  // Rounding can put a real share at zero, which is not the same as no limit.
  it('keeps a share of zero', () => {
    expect(
      projectionNote(
        { overLimit: false, percentOfLimit: 0, total: 100 },
        '2026-08-17T00:00:00Z',
      ),
    ).toBe('Estimated to reach ~100 (0% of your limit) by 16 Aug.')
  })

  it('omits the share when there is no limit', () => {
    expect(
      projectionNote(
        { overLimit: false, percentOfLimit: undefined, total: 100 },
        '2026-08-17T00:00:00Z',
      ),
    ).toBe('Estimated to reach ~100 by 16 Aug.')
  })
})
