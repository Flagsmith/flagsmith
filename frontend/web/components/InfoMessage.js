// import propTypes from 'prop-types';
import React, { PureComponent } from 'react'
import Icon from './Icon'

export default class InfoMessage extends PureComponent {
  static displayName = 'InfoMessage'

  render() {
    const infoMessageClass = `alert alert-info ${
      this.props.infoMessageClass || 'flex-1'
    }`
    return (
      <div className={infoMessageClass}>
        <span className='icon-alert'>
          <Icon name='info' />
        </span>
        <div>
          <div className='title'>{this.props.title || 'NOTE'}</div>
          <div className={`${this.props.infoMessageClass} body`}>
            {this.props.children}
          </div>
        </div>
        <Button className='my-2'>{this.props.buttonText}</Button>
        {this.props.isClosable && (
          <a onClick={this.props.close} className='mt-n2 mr-n2'>
            <span className='icon ion-md-close' />
          </a>
        )}
      </div>
    )
  }
}
