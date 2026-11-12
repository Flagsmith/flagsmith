import React, { PureComponent } from 'react'
import TwoFactor from './SimpleTwoFactor'

export default class TheComponent extends PureComponent {
  static displayName = 'TheComponent'

  static propTypes = {}

  state = {
    pin: '',
  }

  onError = () => this.setState({ error: true })

  render() {
    const { isLoginPage } = this.props
    return (
      <div>
        <AccountProvider>
          {(
            { isSaving, user },
            { confirmTwoFactor, disableTwoFactor, enableTwoFactor },
          ) => (
            <div>
              <TwoFactor
                pin={this.state.pin}
                error={this.state.error}
                onEnable={enableTwoFactor}
                onDisable={disableTwoFactor}
                backupCodes={user.backupCodes}
                hasConfirmed={user.twoFactorConfirmed}
                hasEnabled={user.twoFactorEnabled}
                activationQR={user.twoFactor && user.twoFactor.qr_link}
                activationCode={user.twoFactor && user.twoFactor.secret}
                isLoading={isSaving}
                onChange={(e) =>
                  this.setState({ pin: Utils.safeParseEventValue(e) })
                }
                onRegister={() => {
                  this.setState({ error: null })
                  confirmTwoFactor(
                    this.state.pin,
                    this.onError,
                    isLoginPage || false,
                  )
                }}
              />
            </div>
          )}
        </AccountProvider>
      </div>
    )
  }
}
