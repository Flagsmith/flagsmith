import {
  hasLabelledData,
  aggregateByLabels,
} from 'components/feature-page/FeatureNavTab/utils'
import { Res } from 'common/types/responses'

const MOCK_COLORS = ['#blue', '#red', '#green', '#orange', '#purple']

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

    const result = aggregateByLabels(data, MOCK_COLORS)

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

    const result = aggregateByLabels(data, MOCK_COLORS)

    expect(result.chartData[0]['js-sdk']).toBe(125)
  })

  it('returns unique label values', () => {
    const data: Res['environmentAnalytics'] = [
      { count: 10, day: '2026-04-01', labels: { user_agent: 'js-sdk' } },
      { count: 20, day: '2026-04-01', labels: { user_agent: 'python-sdk' } },
      { count: 30, day: '2026-04-02', labels: { user_agent: 'js-sdk' } },
    ]

    const result = aggregateByLabels(data, MOCK_COLORS)

    expect(result.labelValues).toEqual(['js-sdk', 'python-sdk'])
  })

  it('builds a color map from provided colors', () => {
    const data: Res['environmentAnalytics'] = [
      { count: 10, day: '2026-04-01', labels: { user_agent: 'js-sdk' } },
      { count: 20, day: '2026-04-01', labels: { user_agent: 'python-sdk' } },
    ]

    const result = aggregateByLabels(data, MOCK_COLORS)

    expect(result.colorMap.get('js-sdk')).toBe('#blue')
    expect(result.colorMap.get('python-sdk')).toBe('#red')
  })

  it('wraps colors when more labels than colors', () => {
    const data: Res['environmentAnalytics'] = [
      { count: 1, day: '2026-04-01', labels: { user_agent: 'a' } },
      { count: 1, day: '2026-04-01', labels: { user_agent: 'b' } },
      { count: 1, day: '2026-04-01', labels: { user_agent: 'c' } },
      { count: 1, day: '2026-04-01', labels: { user_agent: 'd' } },
      { count: 1, day: '2026-04-01', labels: { user_agent: 'e' } },
      { count: 1, day: '2026-04-01', labels: { user_agent: 'f' } },
    ]

    const result = aggregateByLabels(data, MOCK_COLORS)

    expect(result.colorMap.get('f')).toBe('#blue') // wraps to index 0
  })

  it('falls back to Unknown when no label value', () => {
    const data: Res['environmentAnalytics'] = [
      { count: 10, day: '2026-04-01', labels: {} },
      { count: 20, day: '2026-04-01' },
    ]

    const result = aggregateByLabels(data, MOCK_COLORS)

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

    const result = aggregateByLabels(data, MOCK_COLORS)

    expect(result.labelValues).toEqual(['js-sdk'])
  })
})
