import type { FetchBaseQueryError } from '@reduxjs/toolkit/query'
import type { SerializedError } from '@reduxjs/toolkit'

export type RequestError = FetchBaseQueryError | SerializedError | undefined

export const isNotFoundError = (error: RequestError) =>
  !!error && 'status' in error && error.status === 404

const hasDetail = (data: unknown): data is { detail: string } =>
  typeof data === 'object' &&
  data !== null &&
  'detail' in data &&
  typeof data.detail === 'string'

// Show the API's detail message on its own, not the whole error object
export const toErrorMessage = (error: RequestError) => {
  if (error && 'data' in error && hasDetail(error.data)) {
    return error.data.detail
  }
  return error
}
