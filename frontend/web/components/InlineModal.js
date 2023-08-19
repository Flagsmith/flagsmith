import propTypes from 'prop-types'
import React, { PureComponent } from 'react'
import cx from 'classnames'
import ModalClose from './modals/base/ModalClose'
import ModalHR from './modals/ModalHR'
import Icon from './Icon'

const enhanceWithClickOutside = require('react-click-outside')

class InlineModal extends PureComponent {
  static displayName = 'Popover'

  static propTypes = {
    bottom: propTypes.node,
    children: propTypes.node,
    isOpen: propTypes.bool,
    onBack: propTypes.func,
    onClose: propTypes.func,
    showBack: propTypes.bool,
    title: propTypes.string,
  }

  handleClickOutside() {
    if (this.props.isOpen) {
      this.props.onClose()
    }
  }

  render() {
    // const { props } = this;
    return (
      <div className='relative'>
        {this.props.isOpen && (
          <div className={cx('inline-modal', this.props.className)}>
            <div className='inline-modal__title'>
              <Row space>
                <Row>
                  {this.props.showBack && (
                    <span
                      onClick={this.props.onBack}
                      className='modal-back-btn clickable'
                    >
                      <Icon name='arrow-left' fill='#9DA4AE' />
                    </span>
                  )}
                  <h5 className='mb-0'>{this.props.title}</h5>
                </Row>
                <ModalClose type='button' onClick={this.props.onClose} />
              </Row>
            </div>
            <ModalHR />
            <div className='inline-modal__content m-4'>
              {this.props.children}
            </div>
            {this.props.bottom && (
              <>
                <ModalHR />
                <div className='inline-modal__bottom m-3'>
                  {this.props.bottom}
                </div>
              </>
            )}
          </div>
        )}
      </div>
    )
  }
}

export default enhanceWithClickOutside(InlineModal)
