import {
  hasLabelledData,
  aggregateByLabels,
} from 'components/feature-page/FeatureNavTab/utils'
import { Res } from 'common/types/responses'
import { CHART_COLOURS } from 'common/theme/tokens'

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

  it('builds a color map by assigning palette colours in label order', () => {
    const data: Res['environmentAnalytics'] = [
      { count: 10, day: '2026-04-01', labels: { user_agent: 'js-sdk' } },
      { count: 20, day: '2026-04-01', labels: { user_agent: 'python-sdk' } },
    ]

    const result = aggregateByLabels(data)

    expect(result.colorMap.get('js-sdk')).toBe(CHART_COLOURS[0])
    expect(result.colorMap.get('python-sdk')).toBe(CHART_COLOURS[1])
  })

  it('wraps colors when more labels than colors in the palette', () => {
    // 11 labels exceeds the 10-colour palette by one → label 11 reuses index 0.
    const data: Res['environmentAnalytics'] = Array.from(
      { length: CHART_COLOURS.length + 1 },
      (_, i) => ({
        count: 1,
        day: '2026-04-01',
        labels: { user_agent: `sdk-${i}` },
      }),
    )

    const result = aggregateByLabels(data)

    expect(result.colorMap.get(`sdk-${CHART_COLOURS.length - 1}`)).toBe(
      CHART_COLOURS[CHART_COLOURS.length - 1],
    )
    expect(result.colorMap.get(`sdk-${CHART_COLOURS.length}`)).toBe(
      CHART_COLOURS[0],
    )
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
