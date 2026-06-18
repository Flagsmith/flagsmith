import React, { FC } from 'react'
import Icon from './icons/Icon'
import Button from './base/forms/Button'
import Format from 'common/utils/format'
import Constants from 'common/constants'

type ErrorMessageProps = {
  enabledButton?: boolean
  error?: any
  errorMessageClass?: string
  errorStyles?: React.CSSProperties
}

const ErrorMessage: FC<ErrorMessageProps> = ({
  enabledButton,
  error: errorProp,
  errorMessageClass,
  errorStyles,
}) => {
  if (!errorProp) return null

  const errorMessageClassName = `alert alert-danger ${
    errorMessageClass || 'flex-1 align-items-center'
  }`
  const error =
    errorProp?.data?.metadata?.find((item: Record<string, unknown>) =>
      // eslint-disable-next-line no-prototype-builtins
      item.hasOwnProperty('non_field_errors'),
    )?.non_field_errors[0] ||
    errorProp?.data ||
    errorProp?.message ||
    errorProp

  return (
    <div
      className={errorMessageClassName}
      style={{
        display: errorMessageClass ? 'initial' : '',
        ...errorStyles,
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
      {enabledButton && (
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
  )
}

export default ErrorMessage
