import { FC } from 'react'
import Banner from './Banner'
import Format from 'common/utils/format'

type ErrorMessageProps = {
  error?: any
}

// The API answers in several shapes: DRF field errors nested under metadata,
// a plain data payload, an Error, or a bare string.
const messageOf = (error: any) =>
  error?.data?.metadata?.find((item: Record<string, unknown>) =>
    Object.prototype.hasOwnProperty.call(item, 'non_field_errors'),
  )?.non_field_errors?.[0] ??
  error?.data ??
  error?.message ??
  error

const renderMessage = (message: any) => {
  if (message instanceof Error) {
    return message.message
  }

  if (typeof message === 'object') {
    return (
      <div
        dangerouslySetInnerHTML={{
          __html: Object.keys(message)
            .map(
              (key) =>
                `${Format.camelCase(Format.enumeration.get(key))}: ${
                  message[key]
                }`,
            )
            .join('<br/>'),
        }}
      />
    )
  }

  return message
}

const ErrorMessage: FC<ErrorMessageProps> = ({ error }) =>
  error ? (
    <Banner variant='danger'>{renderMessage(messageOf(error))}</Banner>
  ) : null

export default ErrorMessage
