// import propTypes from 'prop-types';
import React, { PureComponent } from 'react'

export default class ErrorMessage extends PureComponent {
  static displayName = 'ErrorMessage'

  render() {
    return <div className='alert alert-success'>{this.props.message}</div>
  }
}
