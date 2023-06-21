// import propTypes from 'prop-types';
import React, { PureComponent } from 'react'

export default class InfoMessage extends PureComponent {
  static displayName = 'InfoMessage'

  render() {
    return (
      <div className='alert alert-info'>
        <div className='title'>
          <span
            className={`ion ${this.props.icon || 'ion-ios-information-circle'}`}
          />{' '}
          {this.props.title || 'NOTE'}
        </div>
        {this.props.children}
      </div>
    )
  }
}
