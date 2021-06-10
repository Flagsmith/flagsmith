import propTypes from 'prop-types';
import React, { PureComponent } from 'react';
import cx from 'classnames';

const enhanceWithClickOutside = require('react-click-outside');

class InlineModal extends PureComponent {
  static displayName = 'Popover';

  static propTypes = {
      isOpen: propTypes.bool,
      title: propTypes.string,
      onClose: propTypes.func,
      onBack: propTypes.func,
      showBack: propTypes.bool,
      children: propTypes.node,
  };

  handleClickOutside() {
      if (this.props.isOpen) {
          this.props.onClose();
      }
  }

  render() {
      // const { props } = this;
      return (
          <div className="relative">
              {this.props.isOpen && (
              <div className={cx('inline-modal', 'mt-2', 'px-2', 'pb-2', this.props.className)}>
                  <div className="inline-modal__title mb-2">
                      <Row space>
                          <div>
                              {this.props.showBack && (
                              <button type="button" onClick={this.props.onBack} className="modal-back-btn">
                                  <span className="icon ion-ios-arrow-back"/>
                              </button>
                              )}
                          </div>
                          <Flex className="text-center">
                              {this.props.title}
                          </Flex>
                          <button type="button" onClick={this.props.onClose} className="modal-close-btn">
                              <span className="icon ion-md-close"/>
                          </button>
                      </Row>
                  </div>
                  <div className="inline-modal__content">
                      {this.props.children}
                  </div>
              </div>
              )}
          </div>
      );
  }
}

export default enhanceWithClickOutside(InlineModal);
