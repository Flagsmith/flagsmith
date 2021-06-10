import propTypes from 'prop-types';
import React, { PureComponent } from 'react';
import ErrorMessage from '../ErrorMessage';

export default class TheComponent extends PureComponent {
  static displayName = 'TheComponent';

  static propTypes = {
      isLoading: propTypes.bool,
      error: propTypes.string,
      onSubmit: propTypes.func.isRequired,
      onChange: propTypes.func.isRequired,
      pin: propTypes.string.isRequired,
  };

  render() {
      const { props: {
          onChange,
          error,
          isLoading,
          onSubmit,
          pin,
      } } = this;
      return (
          <Panel
            icon="ion-ios-lock"
            title="Two-Factor Authentication"
          >
              <strong>
              Two-factor authentication code
              </strong>
              <form onSubmit={(e)=>{
                  Utils.preventDefault(e);
                  onSubmit();

              }}>
                  <InputGroup
                    inputProps={{ className: 'full-width', style:{textIndent:0, paddingLeft:10} }}
                    onChange={onChange}
                    value={pin}
                    type="text"
                  />
                  {error && (
                    <ErrorMessage error="Invalid pin code"/>
                  )}
                  <div className="text-right">
                      <Button disabled={isLoading}>
                          Verify Code
                      </Button>
                  </div>
              </form>

              <p className="faint text-center mt-4">
                  Enter the code from the two-factor app on your mobile device. If you've lost your device, you may enter one of your recovery codes.
              </p>
          </Panel>
      );
  }
}
