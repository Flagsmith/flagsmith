import { DDClient, init } from '@datadog/ui-extensions-sdk'
import API from 'project/api'

const client: () => DDClient = () =>
  init({
    authProvider: {
      authStateCallback: async () => {
        const user = API.getCookie('t')
        return {
          isAuthenticated: !!user,
        }
      },
      resolution: 'message',

      /**
       * This where we want Datadog to direct users to authenticate.
       */
      url: '/',
    },
  })
export default client
