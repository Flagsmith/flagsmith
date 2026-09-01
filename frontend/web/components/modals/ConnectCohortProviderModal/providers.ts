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
  docsUrl: string
  // Providers where the user pastes a URL themselves carry an endpoint;
  // Amplitude calls Flagsmith's portal-registered endpoints instead.
  endpoint?: {
    fieldTitle: string
    path: string
  }
  endpointStepTitle: string
  endpointStepBody?: string
  exportStepTitle: string
  exportStepBody: string
}

export const COHORT_PROVIDERS: Record<CohortProviderKey, CohortProviderConfig> =
  {
    amplitude: {
      authRows: [
        { label: 'API key', mono: true, value: '{YOUR_SYNCHRONISATION_KEY}' },
      ],
      docsUrl:
        'https://docs.flagsmith.com/third-party-integrations/cohort-synchronisation/amplitude',
      endpointStepBody:
        'In Amplitude, open Data → Destinations and add Flagsmith as a cohort destination. Paste your synchronisation key when asked for the API key.',
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
      docsUrl:
        'https://docs.flagsmith.com/third-party-integrations/cohort-synchronisation/mixpanel',
      endpoint: {
        fieldTitle: 'Webhook URL',
        path: 'cohort-sync/mixpanel/webhook/',
      },
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
): string | null => {
  const endpoint = COHORT_PROVIDERS[provider].endpoint
  if (!endpoint) {
    return null
  }
  return new URL(
    endpoint.path,
    new URL(Project.api, window.location.origin),
  ).toString()
}
