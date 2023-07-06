// import propTypes from 'prop-types';
import React, { PureComponent } from 'react'
import Icon from './Icon'

export default class ErrorMessage extends PureComponent {
  static displayName = 'ErrorMessage'

  render() {
    return this.props.error ? (
      <div className='alert alert-danger flex-1'>
        <span className='icon-alert'>
          <Icon name='close-circle' />
        </span>
        {typeof this.props.error === 'object'
          ? Object.keys(this.props.error)
              .map((v) => `${v}: ${this.props.error[v]}`)
              .join('\n')
          : this.props.error}
      </div>
    ) : null
  }
}
