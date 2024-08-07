// import propTypes from 'prop-types';
import React, { PureComponent } from 'react'
import Icon from './Icon'
import { close, checkmark } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'

export default class InfoMessage extends PureComponent {
  static displayName = 'InfoMessage'

  handleOpenNewWindow = () => {
    window.open(this.props.url, '_blank')
  }

  render() {
    return (
      <div className={'alert alert-info flex-1'}>
        <span className={`icon-alert info-icon`}>
          <Icon fill={'#0AADDF'} name={this.props.icon || 'info'} />
        </span>
        <div className={'flex-fill'}>
          <div className='title'>{this.props.title || 'NOTE'}</div>
          <div className='flex-fill'>{this.props.children}</div>
        </div>
        {this.props.url && this.props.buttonText && (
          <Button
            size='small'
            className='btn my-2 ml-2'
            onClick={this.handleOpenNewWindow}
          >
            {this.props.buttonText}
          </Button>
        )}
        {this.props.isClosable && (
          <a onClick={this.props.close} className='mt-n2 mr-n2 pl-2'>
            <span className={`icon close-btn`}>
              <IonIcon icon={close} />
            </span>
          </a>
        )}
      </div>
    )
  }
}
