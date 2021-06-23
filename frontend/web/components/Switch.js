// import propTypes from 'prop-types';
import React, { PureComponent } from 'react';
import RCSwitch from 'rc-switch';

export default class Switch extends PureComponent {
  static displayName = 'Switch';

  static propTypes = {};

  render() {
      const { props } = this;

      if (E2E) {
          return (
              <div style={{ height: '28px', display: 'inline-block' }}>
                  <button
                    role="switch"
                    type="button"
                    style={{ color: 'black', position: 'relative', pointerEvents: 'all' }}
                    className={this.props.checked ? 'switch-checked' : 'switch-unchecked'} {...this.props} onClick={() => {
                        this.props.onChange(!this.props.checked);
                    }}
                  >
                      {this.props.checked ? this.props.offMarkup || 'On' : this.props.onMarkup || 'Off'}
                  </button>
              </div>
          );
      }
      return (
          <div style={{ height: '28px', display: 'inline-block', position: 'relative' }}>
              <RCSwitch {...this.props}/>
              {this.props.checked ? <div className="switch-checked">{this.props.offMarkup || 'On'}</div> : (
                  <div className="switch-unchecked">{this.props.onMarkup || 'Off'}</div>
              )}
          </div>
      );
  }
}
