import propTypes from 'prop-types'
import React, { Component } from 'react'
import QRCode from 'qrcode.react'
import ErrorMessage from 'components/ErrorMessage'

export default class TheComponent extends Component {
  static displayName = 'TheComponent'

  static propTypes = {
    activationCode: propTypes.string,
    activationQR: propTypes.string,
    backupCodes: propTypes.array,
    error: propTypes.string,
    hasConfirmed: propTypes.bool.isRequired,
    hasEnabled: propTypes.bool.isRequired,
    isLoading: propTypes.bool.isRequired,
    onChange: propTypes.func.isRequired,
    onDisable: propTypes.func.isRequired,
    onEnable: propTypes.func.isRequired,
    onRegister: propTypes.func.isRequired,
    pin: propTypes.string,
  }

  render() {
    const {
      props: {
        activationCode,
        activationQR,
        backupCodes,
        error,
        hasConfirmed,
        hasEnabled,
        isLoading,
        onChange,
        onDisable,
        onEnable,
        onRegister,
        pin,
      },
    } = this
    return (
      <div>
        {!hasEnabled && (
          <div>
            <div className='text-right'>
              <Button disabled={isLoading} onClick={onEnable}>
                Enable Two-Factor Authentication
              </Button>
            </div>
          </div>
        )}
        {hasEnabled && !hasConfirmed && (
          <div>
            <Row style={{ alignItems: 'flex-start', flexWrap: 'noWrap' }}>
              <div className='mr-2'>
                <QRCode renderAs='svg' size={171} value={activationQR} />
              </div>
              <div className='ml-2 panel--grey'>
                <div className='mb-1'>
                  <strong>Can't scan the code?</strong>
                </div>
                <div>
                  To add the entry manually, provide the following details to
                  the application on your phone. Key:{' '}
                  <strong>{activationCode}</strong>
                </div>
              </div>
            </Row>
            <div>
              <InputGroup
                inputProps={{ className: 'full-width' }}
                onChange={onChange}
                value={pin}
                type='text'
                title='Pin code'
              />
              {error && <ErrorMessage error='Invalid pin code' />}
              <div className='text-right'>
                <Button disabled={isLoading} onClick={onRegister}>
                  Register with two-factor app
                </Button>
              </div>
            </div>
          </div>
        )}

        {hasConfirmed && (
          <div>
            <strong>Two Factor has been enabled</strong>
            <div className='text-right'>
              <Button disabled={isLoading} onClick={onDisable}>
                Disable two-factor
              </Button>
            </div>
            {backupCodes && (
              <div>
                Should you ever lose your phone or access to your one time
                password secret, each of these recovery codes can be used one
                time each to regain access to your account. Please save them in
                a safe place, or you will lose access to your account.
                <ul>
                  {backupCodes.map((code) => (
                    <li key={code}>
                      <strong>{code}</strong>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    )
  }
}
