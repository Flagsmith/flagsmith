// import propTypes from 'prop-types';
import React, { PureComponent } from 'react'
import Icon from './Icon'
import { close } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'

export default class SuccessMessage extends PureComponent {
  static displayName = 'SuccessMessage'

  handleOpenNewWindow = () => {
    window.open(this.props.url, '_blank')
  }

  render() {
    const infoMessageClass = `alert alert-success ${
      this.props.infoMessageClass || 'flex-1'
    }`
    const titleDescClass = this.props.infoMessageClass
      ? `${this.props.infoMessageClass} body mr-2`
      : ''

    return (
      <div className={infoMessageClass}>
        <span className={`icon-alert ${this.props.infoMessageClass} info-icon`}>
          <Icon fill='#27AB95' name='checkmark-circle' />
        </span>
        <div className={titleDescClass}>
          <div className='title'>{this.props.title || 'SUCCESS'}</div>
          {this.props.children}
        </div>
        {this.props.url && (
          <Button className='btn my-2' onClick={this.handleOpenNewWindow}>
            {this.props.buttonText}
          </Button>
        )}
        {this.props.isClosable && (
          <a onClick={this.props.close} className='mt-n2 mr-n2 pl-2'>
            <span className={`icon ${this.props.infoMessageClass} close-btn`}>
              <IonIcon icon={close} />
            </span>
          </a>
        )}
      </div>
    )
  }
}
