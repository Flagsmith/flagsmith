import Project from 'common/project'

export type CohortProviderKey = 'amplitude' | 'mixpanel'

export type CohortProviderAuthRow = {
  label: string
  value: string
  mono?: boolean
}

export type CohortProviderConfig = {
  label: string
  authRows: CohortProviderAuthRow[]
  endpointFieldTitle: string
  endpointPath: string
  endpointStepTitle: string
  exportStepTitle: string
  exportStepBody: string
}

export const COHORT_PROVIDERS: Record<CohortProviderKey, CohortProviderConfig> =
  {
    amplitude: {
      authRows: [
        { label: 'Authentication', value: 'Bearer token' },
        { label: 'Token', mono: true, value: '{YOUR_SYNCHRONISATION_KEY}' },
      ],
      // Amplitude posts cohort list creation here, then adds and removes
      // members under `lists/{list_id}/add` and `lists/{list_id}/remove`.
      endpointFieldTitle: 'List endpoint URL',
      endpointPath: 'cohort-sync/amplitude/lists/',
      endpointStepTitle: 'Add Flagsmith as a destination in Amplitude',
      exportStepBody:
        'In Amplitude, open the cohort you want to target and synchronise it to the Flagsmith destination. Flagsmith creates the managed segment automatically on the first synchronisation, then keeps its members up to date as people enter and leave the cohort.',
      exportStepTitle: 'Synchronise your cohort to Flagsmith',
      label: 'Amplitude',
    },
    mixpanel: {
      authRows: [
        { label: 'Authentication', value: 'Basic auth' },
        { label: 'Username', value: 'Any value' },
        { label: 'Password', mono: true, value: '{YOUR_SYNCHRONISATION_KEY}' },
      ],
      endpointFieldTitle: 'Webhook URL',
      endpointPath: 'cohort-sync/mixpanel/webhook/',
      endpointStepTitle: 'Create a webhook in Mixpanel',
      exportStepBody:
        'In Mixpanel, open the cohort you want to target and export it to the webhook you just created. Flagsmith creates the managed segment automatically on the first synchronisation, then keeps its members up to date as people enter and leave the cohort.',
      exportStepTitle: 'Export your cohort to the webhook',
      label: 'Mixpanel',
    },
  }

// Proxied self-hosted deployments configure a relative Project.api ('/api/v1/');
// providers need an absolute callback URL, so resolve against the page origin.
export const getCohortProviderEndpoint = (
  provider: CohortProviderKey,
): string =>
  new URL(
    COHORT_PROVIDERS[provider].endpointPath,
    new URL(Project.api, window.location.origin),
  ).toString()
