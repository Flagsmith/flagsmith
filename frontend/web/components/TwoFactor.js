// import propTypes from 'prop-types';
import React, { PureComponent } from 'react';
import AccountStore from '../../common/stores/account-store';
import TwoFactor from './SimpleTwoFactor';
import ErrorMessage from './ErrorMessage';

export default class TheComponent extends PureComponent {
  static displayName = 'TheComponent';

  static propTypes = {};

  state = {
      pin: '',
  }

  onError = () => this.setState({ error: true })

  render() {
      // const { props } = this;
      return (
          <div>

              <AccountProvider>
                  {({ isSaving, user }, { enableTwoFactor, disableTwoFactor, confirmTwoFactor }) => (
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
                            onChange={e => this.setState({ pin: Utils.safeParseEventValue(e) })}
                            onRegister={() => {
                                this.setState({ error: null });
                                confirmTwoFactor(this.state.pin, this.onError);
                            }}
                          />
                      </div>
                  )}
              </AccountProvider>
          </div>
      );
  }
}
