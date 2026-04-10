import {
  hasLabelledData,
  aggregateByLabels,
  buildEnvColorMap,
} from 'components/feature-page/FeatureNavTab/utils'
import { Res } from 'common/types/responses'

// Mock getCSSVars since it reads from DOM
jest.mock('common/utils/getCSSVar', () => ({
  getCSSVars: (names: string[]) => names.map((_, i) => `#color-${i}`),
}))

describe('hasLabelledData', () => {
  it('returns false for undefined data', () => {
    expect(hasLabelledData(undefined)).toBe(false)
  })

  it('returns false for empty array', () => {
    expect(hasLabelledData([])).toBe(false)
  })

  it('returns false when no entries have labels', () => {
    const data: Res['environmentAnalytics'] = [
      { count: 10, day: '2026-04-01' },
      { count: 20, day: '2026-04-02' },
    ]
    expect(hasLabelledData(data)).toBe(false)
  })

  it('returns false when labels are null', () => {
    const data: Res['environmentAnalytics'] = [
      { count: 10, day: '2026-04-01', labels: null },
    ]
    expect(hasLabelledData(data)).toBe(false)
  })

  it('returns false when labels are empty object', () => {
    const data: Res['environmentAnalytics'] = [
      { count: 10, day: '2026-04-01', labels: {} },
    ]
    expect(hasLabelledData(data)).toBe(false)
  })

  it('returns true when at least one entry has labels', () => {
    const data: Res['environmentAnalytics'] = [
      { count: 10, day: '2026-04-01' },
      {
        count: 20,
        day: '2026-04-02',
        labels: { user_agent: 'flagsmith-js-sdk' },
      },
    ]
    expect(hasLabelledData(data)).toBe(true)
  })
})

describe('aggregateByLabels', () => {
  it('groups entries by day and label value', () => {
    const data: Res['environmentAnalytics'] = [
      { count: 100, day: '2026-04-01', labels: { user_agent: 'js-sdk' } },
      { count: 200, day: '2026-04-01', labels: { user_agent: 'python-sdk' } },
      { count: 150, day: '2026-04-02', labels: { user_agent: 'js-sdk' } },
    ]

    const result = aggregateByLabels(data)

    expect(result.chartData).toHaveLength(2)
    expect(result.chartData[0]).toEqual({
      day: '2026-04-01',
      'js-sdk': 100,
      'python-sdk': 200,
    })
    expect(result.chartData[1]).toEqual({
      day: '2026-04-02',
      'js-sdk': 150,
    })
  })

  it('accumulates counts for same day + label', () => {
    const data: Res['environmentAnalytics'] = [
      { count: 50, day: '2026-04-01', labels: { user_agent: 'js-sdk' } },
      { count: 75, day: '2026-04-01', labels: { user_agent: 'js-sdk' } },
    ]

    const result = aggregateByLabels(data)

    expect(result.chartData[0]['js-sdk']).toBe(125)
  })

  it('returns unique label values', () => {
    const data: Res['environmentAnalytics'] = [
      { count: 10, day: '2026-04-01', labels: { user_agent: 'js-sdk' } },
      { count: 20, day: '2026-04-01', labels: { user_agent: 'python-sdk' } },
      { count: 30, day: '2026-04-02', labels: { user_agent: 'js-sdk' } },
    ]

    const result = aggregateByLabels(data)

    expect(result.labelValues).toEqual(['js-sdk', 'python-sdk'])
  })

  it('builds a color map for each label', () => {
    const data: Res['environmentAnalytics'] = [
      { count: 10, day: '2026-04-01', labels: { user_agent: 'js-sdk' } },
      { count: 20, day: '2026-04-01', labels: { user_agent: 'python-sdk' } },
    ]

    const result = aggregateByLabels(data)

    expect(result.colorMap.size).toBe(2)
    expect(result.colorMap.has('js-sdk')).toBe(true)
    expect(result.colorMap.has('python-sdk')).toBe(true)
  })

  it('falls back to Unknown when no label value', () => {
    const data: Res['environmentAnalytics'] = [
      { count: 10, day: '2026-04-01', labels: {} },
      { count: 20, day: '2026-04-01' },
    ]

    const result = aggregateByLabels(data)

    expect(result.labelValues).toEqual(['Unknown'])
    expect(result.chartData[0].Unknown).toBe(30)
  })

  it('prefers user_agent over client_application_name', () => {
    const data: Res['environmentAnalytics'] = [
      {
        count: 10,
        day: '2026-04-01',
        labels: { client_application_name: 'my-app', user_agent: 'js-sdk' },
      },
    ]

    const result = aggregateByLabels(data)

    expect(result.labelValues).toEqual(['js-sdk'])
  })
})

describe('buildEnvColorMap', () => {
  it('assigns a color to each environment ID', () => {
    const result = buildEnvColorMap(['env-1', 'env-2', 'env-3'])

    expect(result.size).toBe(3)
    expect(result.get('env-1')).toBe('#color-0')
    expect(result.get('env-2')).toBe('#color-1')
    expect(result.get('env-3')).toBe('#color-2')
  })

  it('wraps colors when more environments than colors', () => {
    const envIds = Array.from({ length: 15 }, (_, i) => `env-${i}`)
    const result = buildEnvColorMap(envIds)

    expect(result.size).toBe(15)
    // Colors wrap around after 10 (mocked CHART_COLOURS has 10 entries)
    expect(result.get('env-0')).toBe(result.get('env-10'))
  })
})
