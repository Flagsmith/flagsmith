export type ChartDataPoint = {
  day: string
  [key: string]: string | number
}

export type BarSeries = {
  /** dataKey to read from each `ChartDataPoint`. */
  key: string
  label: string
  colour: string
  /**
   * Bars sharing a stack id stack on top of each other; distinct ids sit side
   * by side. Defaults to one shared stack, so a chart that says nothing gets a
   * single stacked bar per x value.
   */
  stackId?: string
  /**
   * SVG fill-opacity (0-1), for the faded part of a part-of-whole bar. Colours
   * can be CSS `var()` strings, so transparency can't come from an alpha
   * channel. The legend swatch matches it.
   */
  opacity?: number
}
