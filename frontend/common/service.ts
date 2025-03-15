import {
  BaseQueryApi,
  createApi,
  fetchBaseQuery,
} from '@reduxjs/toolkit/dist/query/react'

import {
  FetchArgs,
  FetchBaseQueryArgs,
} from '@reduxjs/toolkit/dist/query/fetchBaseQuery'
import { CreateApiOptions } from '@reduxjs/toolkit/dist/query/createApi'
import { StoreStateType } from './store'

const Project = require('./project')
const _data = require('./data/base/_data.js')

const excludedEndpoints = [
  'register',
  'createConfirmEmail',
  'createResetPassword',
  'createResendConfirmationEmail',
  'createForgotPassword',
]

const refreshAccessToken = async () => {
  try {
    const response = await fetch(`${Project.api}auth/token/refresh/`, {
      credentials: 'include',
      method: 'POST',
    })

    if (!response.ok) {
      throw new Error('Failed to refresh token')
    }

    return
  } catch (error) {
    console.error('Token refresh failed', error)
    throw error
  }
}

export const baseApiOptions = (queryArgs?: Partial<FetchBaseQueryArgs>) => {
  const baseQuery = fetchBaseQuery({
    baseUrl: Project.api,
    credentials: Project.cookieAuthEnabled ? 'include' : undefined,
    prepareHeaders: async (headers, { endpoint, getState }) => {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const state = getState() as StoreStateType
      if (!excludedEndpoints.includes(endpoint)) {
        try {
          const token = _data.token
          if (token && !Project.cookieAuthEnabled) {
            headers.set('Authorization', `Token ${token}`)
          }
        } catch (e) {}
      }

      return headers
    },
    ...queryArgs,
  })

  const baseQueryWithInterceptor = async (
    args: string | FetchArgs,
    api: BaseQueryApi,
    extraOptions: {},
  ) => {
    const result = await baseQuery(args, api, extraOptions)
    if (
      Project.cookieAuthEnabled &&
      result.error &&
      result.error.status === 401
    ) {
      await refreshAccessToken()
      return baseQuery(args, api, extraOptions)
    }
    return result
  }

  const res: Pick<
    CreateApiOptions<any, any, any, any>,
    | 'baseQuery'
    | 'refetchOnReconnect'
    | 'refetchOnFocus'
    | 'extractRehydrationInfo'
  > = {
    baseQuery: baseQueryWithInterceptor,
  }

  return res
}

export const service = createApi({
  ...baseApiOptions(),
  endpoints: () => ({}),
  reducerPath: 'service',
})
