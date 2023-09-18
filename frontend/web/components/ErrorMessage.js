// import propTypes from 'prop-types';
import React, { PureComponent } from 'react'
import Icon from './Icon'
import PaymentModal from './modals/Payment'

export default class ErrorMessage extends PureComponent {
  static displayName = 'ErrorMessage'

  render() {
    const errorMessageClassName = `alert alert-danger ${
      this.props.errorMessageClass || 'flex-1 align-items-center'
    }`
    return this.props.error ? (
      <div
        className={errorMessageClassName}
        style={{ display: this.props.errorMessageClass ? 'initial' : '' }}
      >
        <span className='icon-alert'>
          <Icon name='close-circle' />
        </span>
        {typeof this.props.error === 'object'
          ? Object.keys(this.props.error)
              .map((v) => `${v}: ${this.props.error[v]}`)
              .join('\n')
          : this.props.error}
        {this.props.enabledButton && (
          <Button
            className='btn ml-3'
            onClick={() => {
              openModal(
                'Payment plans',
                <PaymentModal viewOnly={false} />,
                'modal-lg',
              )
            }}
          >
            Upgrade plan
          </Button>
        )}
      </div>
    ) : null
  }
}
