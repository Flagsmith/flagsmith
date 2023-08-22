// import propTypes from 'prop-types';
import React, { PureComponent } from 'react'
import RCSwitch from 'rc-switch'
import Icon from './Icon'

export default class Switch extends PureComponent {
  static displayName = 'Switch'

  static propTypes = {}

  render() {
    const { checked, darkMode, offMarkup, onChange, onMarkup } = this.props
    if (E2E) {
      return (
        <div style={{ display: 'inline-block', height: '28px' }}>
          <button
            role='switch'
            type='button'
            style={{
              color: 'black',
              pointerEvents: 'all',
              position: 'relative',
            }}
            className={checked ? 'switch-checked' : 'switch-unchecked'}
            {...this.props}
            onClick={() => {
              onChange(!this.props.checked)
            }}
          >
            {checked ? offMarkup || 'On' : onMarkup || 'Off'}
          </button>
        </div>
      )
    }
    if (darkMode) {
      return (
        <button
          role='switch'
          type='button'
          className={`rc-switch flex-row justify-content-center gap-3 ${
            checked ? 'rc-switch-checked' : 'rc-switch-unchecked'
          }`}
          {...this.props}
          onClick={() => {
            onChange(!checked)
          }}
        >
          <Icon name='sun' fill={checked ? '#656D7B' : '#1A2634'} />
          <Icon name='moon' fill={checked ? '#FFFFFF' : '#9DA4AE'} />
        </button>
      )
    }
    return <RCSwitch {...this.props} />
  }
}
