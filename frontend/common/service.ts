import * as amplitude from '@amplitude/analytics-browser'
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/dist/query/react'

import { FetchBaseQueryArgs } from '@reduxjs/toolkit/dist/query/fetchBaseQuery'
import { CreateApiOptions } from '@reduxjs/toolkit/dist/query/createApi'
import { StoreStateType } from './store'

import Project from './project'
import _data from './data/base/_data'

const baseApiOptions = (queryArgs?: Partial<FetchBaseQueryArgs>) => {
  const res: Pick<
    CreateApiOptions<any, any, any, any>,
    | 'baseQuery'
    | 'refetchOnReconnect'
    | 'refetchOnFocus'
    | 'extractRehydrationInfo'
  > = {
    baseQuery: fetchBaseQuery({
      baseUrl: Project.api,
      credentials: Project.cookieAuthEnabled ? 'include' : undefined,
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
            if (token && !Project.cookieAuthEnabled) {
              headers.set('Authorization', `Token ${token}`)
            }
          } catch (e) {}
        }

        const deviceId = amplitude.getDeviceId()
        const sessionId = amplitude.getSessionId()
        const userId = amplitude.getUserId()
        if (deviceId || sessionId || userId) {
          const entries: string[] = []
          if (deviceId) entries.push(`amplitude.device_id=${deviceId}`)
          if (sessionId) entries.push(`amplitude.session_id=${sessionId}`)
          if (userId) entries.push(`amplitude.user_id=${userId}`)
          headers.set('baggage', entries.join(','))
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
