import {
  meterCopy,
  meterTone,
} from 'components/pages/usage/components/UsageMeter/utils'

describe('UsageMeter utils', () => {
  describe('meterCopy', () => {
    it('reads as a percentage of the limit when there is one', () => {
      expect(meterCopy(1500000, 2000000)).toEqual({
        fraction: {
          caption: 'API calls used / plan limit',
          suffix: ' / 2M',
          value: '1.5M',
        },
        headline: '75%',
        headlineCaption: 'of plan consumed',
      })
    })

    it('reports past 100% rather than capping', () => {
      expect(meterCopy(2400000, 2000000).headline).toBe('120%')
    })

    // Self-hosted has no subscription data, so there is nothing to divide by.
    it.each([[null], [undefined], [0]])(
      'falls back to the raw count when the limit is %p',
      (limit) => {
        expect(meterCopy(1500000, limit)).toEqual({
          headline: '1.5M',
          headlineCaption: 'API calls',
        })
      },
    )

    it('shows zero rather than NaN for an organisation with no calls', () => {
      expect(meterCopy(0, null).headline).toBe('0')
      expect(meterCopy(0, 2000000).headline).toBe('0%')
    })
  })

  describe('meterTone', () => {
    it('tracks the thresholds when the comparison holds', () => {
      expect(meterTone(500000, 2000000, 75)).toBe('success')
      expect(meterTone(1600000, 2000000, 75)).toBe('warning')
      expect(meterTone(2000000, 2000000, 75)).toBe('danger')
    })

    it('has no tone to give without a limit', () => {
      expect(meterTone(9000000, null, 75)).toBeUndefined()
    })
  })
})
