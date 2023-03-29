import propTypes from 'prop-types'
import React, { PureComponent } from 'react'
import ErrorMessage from 'components/ErrorMessage'

export default class TheComponent extends PureComponent {
  static displayName = 'TheComponent'

  static propTypes = {
    error: propTypes.string,
    isLoading: propTypes.bool,
    onChange: propTypes.func.isRequired,
    onSubmit: propTypes.func.isRequired,
    pin: propTypes.string.isRequired,
  }

  render() {
    const {
      props: { error, isLoading, onChange, onSubmit, pin },
    } = this
    return (
      <Panel icon='ion-ios-lock' title='Two-Factor Authentication'>
        <strong>Two-factor authentication code</strong>
        <form
          onSubmit={(e) => {
            Utils.preventDefault(e)
            onSubmit()
          }}
        >
          <InputGroup
            inputProps={{
              className: 'full-width',
              style: { paddingLeft: 10, textIndent: 0 },
            }}
            onChange={onChange}
            value={pin}
            type='text'
          />
          {error && <ErrorMessage error='Invalid pin code' />}
          <div className='text-right'>
            <Button disabled={isLoading}>Verify Code</Button>
          </div>
        </form>

        <p className='faint text-center mt-4'>
          Enter the code from the two-factor app on your mobile device. If
          you've lost your device, you may enter one of your recovery codes.
        </p>
      </Panel>
    )
  }
}
