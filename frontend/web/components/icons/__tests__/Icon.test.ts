import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import Icon, { IconName } from 'components/icons/Icon'

const render = (name: IconName) =>
  renderToStaticMarkup(
    createElement(Icon, { 'aria-label': 'Label', className: 'ms-1', name }),
  )

describe('Icon', () => {
  it.each`
    name           | case
    ${'warning'}   | ${'a case that ignored the rest props'}
    ${'code'}      | ${'a case that spread them already'}
    ${'pr-merged'} | ${'a case with its own class'}
  `('applies className and aria props on $case', ({ name }) => {
    expect(render(name)).toMatch(/^<svg[^>]*class="[^"]*\bms-1\b/)
    expect(render(name)).toMatch(/^<svg[^>]*aria-label="Label"/)
  })

  it('keeps the class a case sets itself', () => {
    expect(render('pr-merged')).toMatch(/^<svg[^>]*class="ml-1 ms-1"/)
  })
})
