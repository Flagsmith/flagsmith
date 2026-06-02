import { createFlagsmithInstance } from '@flagsmith/flagsmith/isomorphic'
import Project from 'common/project'

// Emits a throwaway "test_custom_event" tagged with the target environment's
// client-side key, so the user can verify their warehouse connection. A
// dedicated instance is used because the dashboard's global Flagsmith client is
// keyed to Flagsmith's own environment, not the customer's.
//
// We only want to emit an event, never evaluate flags. `preventFetch` with an
// empty `defaultFlags` skips fetching the customer's flag configuration
// entirely (so we never pull their config into the dashboard), while
// `enableEvents` still starts the event pipeline. `api` targets the backend
// this environment lives on, and `eventsApiUrl` (when configured) points the
// event pipeline at the matching ingestor; otherwise the SDK default is used.
const sendWarehouseTestEvent = async (environmentId: string): Promise<void> => {
  const instance = createFlagsmithInstance()
  await instance.init({
    api: Project.api,
    defaultFlags: {},
    enableEvents: true,
    environmentID: environmentId,
    preventFetch: true,
    ...(Project.flagsmithClientEventsAPI && {
      eventProcessorConfig: {
        eventsApiUrl: Project.flagsmithClientEventsAPI,
      },
    }),
  })
  instance.trackEvent('test_custom_event')
}

export default sendWarehouseTestEvent
