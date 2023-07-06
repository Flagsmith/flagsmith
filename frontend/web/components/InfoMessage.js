// import propTypes from 'prop-types';
import React, { PureComponent } from 'react'
import Icon from './Icon'

export default class InfoMessage extends PureComponent {
  static displayName = 'InfoMessage'

  render() {
    return (
      <div className='alert alert-info flex-1'>
        <span className='icon-alert'>
          <Icon name='info' />
        </span>
        <div>
          <div className='title'>{this.props.title || 'NOTE'}</div>
          {this.props.children}
        </div>
      </div>
    )
  }
}
