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
    const error = this.props.error?.data || this.props.error
    return this.props.error ? (
      <div
        className={errorMessageClassName}
        style={{ display: this.props.errorMessageClass ? 'initial' : '' }}
      >
        <span className='icon-alert'>
          <Icon name='close-circle' />
        </span>
        {typeof error === 'object' ? (
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
        ) : this.props.exceeded ? (
          <>
            Your organisation has exceeded its API usage quota {`(${error}).`}{' '}
            {Utils.getPlanName(this.props.organisationPlan) === 'Free' ? (
              <b>Please upgrade your plan to continue receiving service.</b>
            ) : (
              <b>Automated billing for the overages may apply.</b>
            )}
          </>
        ) : (
          error
        )}
        {this.props.enabledButton && (
          <Button
            className='btn ml-3'
            onClick={() => {
              document.location.replace(Constants.upgradeURL)
            }}
          >
            Upgrade plan
          </Button>
        )}
      </div>
    ) : null
  }
}
