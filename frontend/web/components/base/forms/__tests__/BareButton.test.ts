import { BareButton, BareButtonProps } from 'components/base/forms/BareButton'

describe('BareButton', () => {
  it('exports a named component with a displayName', () => {
    expect(BareButton).toBeDefined()
    expect(BareButton.displayName).toBe('BareButton')
  })

  it('supports ref forwarding via $$typeof (forwardRef component)', () => {
    // React.forwardRef wraps the component in an object with $$typeof
    // equal to Symbol.for('react.forward_ref')
    expect((BareButton as any).$$typeof).toBe(Symbol.for('react.forward_ref'))
  })

  it('is also available as a default export', async () => {
    const mod = await import('components/base/forms/BareButton')
    expect(mod.default).toBe(BareButton)
  })

  // Type-level check: ensure BareButtonProps extends standard button attrs.
  // This is a compile-time test — if it compiles, the contract is correct.
  it('has a BareButtonProps type that is assignable from standard button attributes', () => {
    const props: BareButtonProps = {
      'aria-label': 'test',
      'disabled': true,
      'onClick': () => {},
      'type': 'button',
    }
    expect(props.type).toBe('button')
  })
})
