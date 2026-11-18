// Throwaway: checks the review lint rules from #8819 warn in CI. Never merge.
import { FC } from 'react'
import ErrorMessage from './ErrorMessage'

type Shape = { a: number }

const LintRulesCheck: FC<{ value?: unknown; maybe?: Shape }> = ({
  maybe,
  value,
}) => {
  // Expect a warning: type assertion
  const shape = value as Shape
  // No warning: as const
  const sizes = ['sm', 'lg'] as const
  // Expect a warning: non-null assertion
  const a = maybe!.a
  // Expect a warning: hex literal
  const hex = '#ff0000'
  // Expect a warning: rgb in a template
  const rgb = `rgb(${a}, 0, 0)`
  // Expect two warnings: fetch and window.fetch
  fetch('/api')
  window.fetch('/api')

  return (
    <div>
      {/* Expect a warning: style object */}
      <div style={{ color: 'red' }} />
      {/* No warning: custom property only */}
      <div style={{ '--w': '1px' }} />
      {/* Expect a warning: data-test */}
      <div data-test='check' />
      {/* Expect a warning: role='button' */}
      <div role='button' />
      {/* Expect warnings: legacy chip and alert classes */}
      <span className='chip' />
      <div className='alert' />
      <ErrorMessage error='x' />
      {shape.a}
      {sizes[0]}
      {hex}
      {rgb}
    </div>
  )
}

export default LintRulesCheck
