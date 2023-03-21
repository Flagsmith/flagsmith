import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/dist/query/react'

import { FetchBaseQueryArgs } from '@reduxjs/toolkit/dist/query/fetchBaseQuery'
import { CreateApiOptions } from '@reduxjs/toolkit/dist/query/createApi'
import { StoreStateType } from './store'

const Project = require('./project')
const _data = require('./data/base/_data.js')

export const baseApiOptions = (queryArgs?: Partial<FetchBaseQueryArgs>) => {
  const res: Pick<
    CreateApiOptions<any, any, any, any>,
    | 'baseQuery'
    | 'refetchOnReconnect'
    | 'refetchOnFocus'
    | 'extractRehydrationInfo'
  > = {
    baseQuery: fetchBaseQuery({
      baseUrl: Project.api,
      prepareHeaders: async (headers, { endpoint, getState }) => {
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        const state = getState() as StoreStateType
        if (
          endpoint !== 'register' &&
          endpoint !== 'createConfirmEmail' &&
          endpoint !== 'createResetPassword' &&
          endpoint !== 'createResendConfirmationEmail' &&
          endpoint !== 'createForgotPassword'
        ) {
          try {
            const token = _data.token
            if (token) {
              headers.set('Authorization', `Token ${token}`)
            }
          } catch (e) {}
        }

        return headers
      },
      ...queryArgs,
    }),

    refetchOnFocus: true,
    refetchOnReconnect: true,
  }
  return res
}

export const service = createApi({
  ...baseApiOptions(),
  endpoints: () => ({}),
  reducerPath: 'service',
})
