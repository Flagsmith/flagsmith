// import propTypes from 'prop-types';
import React, { PureComponent } from 'react'
import Icon from './Icon'
import Button from './base/forms/Button'
import Format from 'common/utils/format'
import Constants from 'common/constants'

export default class ErrorMessage extends PureComponent {
  static displayName = 'ErrorMessage'

  render() {
    const errorMessageClassName = `alert alert-danger ${
      this.props.errorMessageClass || 'flex-1 align-items-center'
    }`
    const error =
      this.props.error?.data?.metadata?.find((item) =>
        // eslint-disable-next-line no-prototype-builtins
        item.hasOwnProperty('non_field_errors'),
      )?.non_field_errors[0] ||
      this.props.error?.data ||
      this.props.error?.message ||
      this.props.error
    return this.props.error ? (
      <div
        className={errorMessageClassName}
        style={{
          display: this.props.errorMessageClass ? 'initial' : '',
          ...this.props.errorStyles,
        }}
      >
        <span className='icon-alert'>
          <Icon name='close-circle' />
        </span>
        {error instanceof Error ? (
          error.message
        ) : typeof error === 'object' ? (
          <div
            dangerouslySetInnerHTML={{
              __html: Object.keys(error)
                .map(
                  (v) =>
                    `${Format.camelCase(Format.enumeration.get(v))}: ${
                      error[v]
                    }`,
                )
                .join('<br/>'),
            }}
          />
        ) : (
          error
        )}
        {this.props.enabledButton && (
          <Button
            className='btn ml-3'
            onClick={() => {
              document.location.replace(Constants.getUpgradeUrl())
            }}
          >
            Upgrade plan
          </Button>
        )}
      </div>
    ) : null
  }
}
