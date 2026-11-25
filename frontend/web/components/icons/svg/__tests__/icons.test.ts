import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import * as icons from './..'
import type { IconComponent } from './..'

const ICONS = Object.entries(icons).filter(
  (entry): entry is [string, IconComponent] => typeof entry[1] === 'function',
)

const render = (Svg: IconComponent) =>
  renderToStaticMarkup(
    createElement(Svg, {
      'aria-label': 'Label',
      className: 'ms-1',
      fill: 'red',
    }),
  )

describe('icon library', () => {
  it.each(ICONS)('%s sits on the 24px grid', (_, Svg) => {
    expect(render(Svg)).toMatch(/^<svg[^>]*viewBox="0 0 24 24"/)
  })

  it.each(ICONS)('%s applies className and aria props', (_, Svg) => {
    expect(render(Svg)).toMatch(
      /^<svg[^>]*class="ms-1"[^>]*aria-label="Label"|^<svg[^>]*aria-label="Label"[^>]*class="ms-1"/,
    )
  })

  it.each(ICONS)('%s draws only in the given colour', (_, Svg) => {
    const colours = render(Svg).match(/(?:stroke|fill)="([^"]+)"/g) ?? []
    expect(colours.filter((c) => !/="(red|none)"$/.test(c))).toEqual([])
  })
})
