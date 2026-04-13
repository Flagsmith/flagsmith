import { buildChartColorMap } from 'components/charts/buildChartColorMap'
import { CHART_COLOURS } from 'common/theme/tokens'

describe('buildChartColorMap', () => {
  it('maps each label to a palette colour in order', () => {
    const map = buildChartColorMap(['a', 'b', 'c'])

    expect(map.get('a')).toBe(CHART_COLOURS[0])
    expect(map.get('b')).toBe(CHART_COLOURS[1])
    expect(map.get('c')).toBe(CHART_COLOURS[2])
  })

  it('wraps around when there are more labels than palette colours', () => {
    const labels = Array.from(
      { length: CHART_COLOURS.length + 2 },
      (_, i) => `label-${i}`,
    )

    const map = buildChartColorMap(labels)

    expect(map.get(`label-${CHART_COLOURS.length - 1}`)).toBe(
      CHART_COLOURS[CHART_COLOURS.length - 1],
    )
    expect(map.get(`label-${CHART_COLOURS.length}`)).toBe(CHART_COLOURS[0])
    expect(map.get(`label-${CHART_COLOURS.length + 1}`)).toBe(CHART_COLOURS[1])
  })

  it('returns an empty map for no labels', () => {
    const map = buildChartColorMap([])

    expect(map.size).toBe(0)
  })
})
