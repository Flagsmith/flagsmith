import React from 'react'
import Icon from 'components/Icon'
import Button from 'components/base/forms/Button'
import Format from 'common/utils/format'
import Constants from 'common/constants'

interface ErrorMessageProps {
  error?: any
  className?: string
  errorStyles?: React.CSSProperties
  enabledButton?: boolean
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({
  enabledButton,
  error,
  className,
  errorStyles,
}) => {
  const errorMessageClassName = `alert alert-danger ${
    className || 'flex-1 align-items-center'
  }`

  const resolvedError =
    error?.data?.metadata?.find((item: any) =>
      Object.prototype.hasOwnProperty.call(item, 'non_field_errors'),
    )?.non_field_errors?.[0] ??
    error?.data ??
    error?.message ??
    error

  if (!error) return null

  return (
    <div
      className={errorMessageClassName}
      style={{
        display: className ? 'initial' : '',
        ...errorStyles,
      }}
    >
      <span className='icon-alert'>
        <Icon name='close-circle' />
      </span>
      {resolvedError instanceof Error ? (
        resolvedError.message
      ) : typeof resolvedError === 'object' ? (
        <div
          dangerouslySetInnerHTML={{
            __html: Object.keys(resolvedError)
              .map(
                (v) =>
                  `${Format.camelCase(Format.enumeration.get(v))}: ${
                    resolvedError[v]
                  }`,
              )
              .join('<br/>'),
          }}
        />
      ) : (
        resolvedError
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

ErrorMessage.displayName = 'ErrorMessage'

export default ErrorMessage
