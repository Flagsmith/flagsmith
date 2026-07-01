const defaultFlags = {
  integration_data: {
    'amplitude': {
      'categories': ['Analytics'],
      'description': 'Sends data on what flags served to each identity.',
      'docs': 'https://docs.flagsmith.com/integrations/analytics/amplitude',
      'fields': [
        {
          'hidden': true,
          'key': 'api_key',
          'label': 'API Key',
        },
        {
          'key': 'base_url',
          'label': 'Base URL',
        },
      ],
      'image': '/static/images/integrations/amplitude.svg',
      'perEnvironment': true,
      'project': true,
      'title': 'Amplitude',
    },
    'backstage': {
      'categories': ['Enterprise tools'],
      'description':
        'View your Flagsmith feature flags inside your Backstage developer portal.',
      'docs': 'https://docs.flagsmith.com/third-party-integrations/backstage',
      'external': true,
      'image': '/static/images/integrations/backstage.svg',
      'perEnvironment': false,
      'title': 'Backstage',
    },
    'code-references': {
      'categories': ['Developer tools'],
      'description':
        'Integrate with Code References to track feature flag usage in your codebase, and unlock new functionality in Flagsmith.',
      'docs': 'https://docs.flagsmith.com/managing-flags/code-references',
      'external': true,
      'image': '/static/images/integrations/code-references.svg',
      'perEnvironment': false,
      'title': 'Code References',
    },
    'datadog': {
      'categories': ['Monitoring'],
      'description':
        'Sends events to Datadog for when flags are created, updated and removed. Logs are tagged with the environment they came from e.g. production.',
      'docs': 'https://docs.flagsmith.com/integrations/apm/datadog',
      'fields': [
        {
          'key': 'base_url',
          'label': 'Base URL',
        },
        {
          'hidden': true,
          'key': 'api_key',
          'label': 'API Key',
        },
        {
          'default': true,
          'inputType': 'checkbox',
          'key': 'use_custom_source',
          'label': 'Use Custom Source',
        },
      ],
      'image': '/static/images/integrations/datadog.svg',
      'perEnvironment': false,
      'project': true,
      'title': 'Datadog',
    },
    'dynatrace': {
      'categories': ['Monitoring'],
      'description':
        'Sends events to Dynatrace for when flags are created, updated and removed. Logs are tagged with the environment they came from e.g. production.',
      'docs': 'https://docs.flagsmith.com/integrations/apm/dynatrace',
      'fields': [
        {
          'key': 'base_url',
          'label': 'Base URL',
        },
        {
          'hidden': true,
          'key': 'api_key',
          'label': 'API Key',
        },
        {
          'key': 'entity_selector',
          'label': 'Entity Selector',
        },
      ],
      'image': '/static/images/integrations/dynatrace.svg',
      'perEnvironment': true,
      'project': true,
      'title': 'Dynatrace',
    },
    'github': {
      'categories': ['CI/CD'],
      'description':
        'View your Flagsmith Flags inside your GitHub Issues and Pull Request.',
      'docs':
        'https://docs.flagsmith.com/integrations/project-management/github',
      'external': true,
      'image': '/static/images/integrations/github.svg',
      'isExternalInstallation': true,
      'organisation': true,
      'perEnvironment': false,
      'title': 'GitHub',
    },
    'gitlab': {
      'categories': ['CI/CD'],
      'description': 'Link GitLab issues and merge requests to feature flags.',
      'docs':
        'https://docs.flagsmith.com/third-party-integrations/project-management/gitlab',
      'fields': [
        {
          'default': 'https://gitlab.com',
          'key': 'gitlab_instance_url',
          'label': 'GitLab Instance URL',
        },
        {
          'hidden': true,
          'key': 'access_token',
          'label': 'Access Token',
        },
        {
          'default': false,
          'inputType': 'checkbox',
          'key': 'labeling_enabled',
          'label': 'Add "Flagsmith Feature" label to linked issues and MRs',
        },
      ],
      'image': '/static/images/integrations/gitlab.svg',
      'perEnvironment': false,
      'project': true,
      'title': 'GitLab',
    },
    'grafana': {
      'categories': ['Monitoring'],
      'description':
        'Receive Flagsmith annotations to your Grafana instance on feature flag and segment changes.',
      'docs': 'https://docs.flagsmith.com/integrations/apm/grafana',
      'fields': [
        {
          'default': 'https://grafana.com',
          'key': 'base_url',
          'label': 'Base URL',
        },
        {
          'hidden': true,
          'key': 'api_key',
          'label': 'Service account token',
        },
      ],
      'image': '/static/images/integrations/grafana.svg',
      'organisation': true,
      'perEnvironment': false,
      'project': true,
      'title': 'Grafana',
    },
    'heap': {
      'categories': ['Analytics'],
      'description': 'Sends data on what flags served to each identity.',
      'docs': 'https://docs.flagsmith.com/integrations/analytics/heap',
      'fields': [
        {
          'hidden': true,
          'key': 'api_key',
          'label': 'API Key',
        },
        {
          'default': 'https://heapanalytics.com',
          'key': 'base_url',
          'label': 'Base URL',
          'options': [
            {
              'label': 'US',
              'value': 'https://heapanalytics.com',
            },
            {
              'label': 'EU',
              'value': 'https://c.eu.heap-api.com',
            },
          ],
        },
      ],
      'image': '/static/images/integrations/heap.svg',
      'perEnvironment': true,
      'project': true,
      'title': 'Heap Analytics',
    },
    'jira': {
      'categories': ['Project Management'],
      'description': 'View your Flagsmith Flags inside Jira.',
      'docs': 'https://docs.flagsmith.com/integrations/project-management/jira',
      'external': true,
      'image': '/static/images/integrations/jira.svg',
      'organisation': true,
      'perEnvironment': false,
      'project': true,
      'title': 'Jira',
    },
    'mcp': {
      'categories': ['AI'],
      'customUI': true,
      'description':
        'Allow AI assistants and agents to interact with your feature flag infrastructure, including managing flags, segments, and release workflows.',
      'docs':
        'https://docs.flagsmith.com/integrating-with-flagsmith/mcp-server',
      'external': false,
      'image': '/static/images/integrations/mcp.svg',
      'organisation': true,
      'title': 'Flagsmith MCP Server',
    },
    'mixpanel': {
      'categories': ['Analytics'],
      'description': 'Sends data on what flags served to each identity.',
      'docs': 'https://docs.flagsmith.com/integrations/analytics/mixpanel',
      'fields': [
        {
          'hidden': true,
          'key': 'api_key',
          'label': 'Project Token',
        },
        {
          'default': 'https://api.mixpanel.com',
          'key': 'base_url',
          'label': 'Base URL',
          'options': [
            {
              'label': 'US',
              'value': 'https://api.mixpanel.com',
            },
            {
              'label': 'EU',
              'value': 'https://api-eu.mixpanel.com',
            },
            {
              'label': 'India',
              'value': 'https://api-in.mixpanel.com',
            },
          ],
        },
      ],
      'image': '/static/images/integrations/mp.svg',
      'perEnvironment': true,
      'project': true,
      'title': 'Mixpanel',
    },
    'new-relic': {
      'categories': ['Monitoring'],
      'description':
        'Sends events to New Relic for when flags are created, updated and removed.',
      'docs': 'https://docs.flagsmith.com/integrations/apm/newrelic',
      'fields': [
        {
          'key': 'base_url',
          'label': 'New Relic Base URL',
        },
        {
          'hidden': true,
          'key': 'api_key',
          'label': 'New Relic API Key',
        },
        {
          'key': 'app_id',
          'label': 'New Relic Application ID',
        },
      ],
      'image': '/static/images/integrations/new_relic.svg',
      'perEnvironment': false,
      'project': true,
      'title': 'New Relic',
    },
    'rudderstack': {
      'categories': ['Analytics'],
      'description': 'Sends data on what flags served to each identity.',
      'docs': 'https://docs.flagsmith.com/integrations/analytics/rudderstack',
      'fields': [
        {
          'key': 'base_url',
          'label': 'Rudderstack Data Plane URL',
        },
        {
          'hidden': true,
          'key': 'api_key',
          'label': 'API Key',
        },
      ],
      'image': '/static/images/integrations/rudderstack.svg',
      'perEnvironment': true,
      'project': true,
      'title': 'Rudderstack',
    },
    'segment': {
      'categories': ['Analytics'],
      'description': 'Sends data on what flags served to each identity.',
      'docs': 'https://docs.flagsmith.com/integrations/analytics/segment',
      'fields': [
        {
          'hidden': true,
          'key': 'api_key',
          'label': 'API Key',
        },
      ],
      'image': '/static/images/integrations/segment.svg',
      'perEnvironment': true,
      'project': true,
      'title': 'Segment',
    },
    'sentry': {
      'categories': ['Monitoring'],
      'description': 'Send flag change events to Sentry.',
      'docs': 'https://docs.flagsmith.com/integrations/apm/sentry',
      'fields': [
        {
          'key': 'webhook_url',
          'label': 'Webhook URL',
        },
        {
          'hidden': true,
          'key': 'secret',
          'label': 'Secret',
        },
      ],
      'image': '/static/images/integrations/sentry.svg',
      'perEnvironment': true,
      'title': 'Sentry',
    },
    'slack': {
      'categories': ['Messaging'],
      'description':
        'Sends messages to Slack when flags are created, updated and removed. Logs are tagged with the environment they came from e.g. production.',
      'docs': 'https://docs.flagsmith.com/integrations/slack',
      'image': '/static/images/integrations/slack.svg',
      'isOauth': true,
      'perEnvironment': true,
      'project': true,
      'title': 'Slack',
    },
    'webhook': {
      'categories': ['Webhooks'],
      'description':
        'Sends data on what flags served to each identity to a Webhook Endpoint you provide.',
      'docs': 'https://docs.flagsmith.com/integrations/webhook',
      'fields': [
        {
          'key': 'url',
          'label': 'Your Webhook URL Endpoint',
        },
        {
          'hidden': true,
          'key': 'secret',
          'label': 'Your Webhook Secret',
        },
      ],
      'image': '/static/images/integrations/webhooks.svg',
      'perEnvironment': true,
      'project': true,
      'title': 'Webhook',
    },
  },
  segment_operators: [
    {
      'label': 'Exactly Matches (=)',
      'value': 'EQUAL',
    },
    {
      'label': 'Does not match (!=)',
      'value': 'NOT_EQUAL',
    },
    {
      'label': '% Split',
      'value': 'PERCENTAGE_SPLIT',
    },
    {
      'label': '>',
      'type': 'number',
      'value': 'GREATER_THAN',
    },
    {
      'label': '>=',
      'type': 'number',
      'value': 'GREATER_THAN_INCLUSIVE',
    },
    {
      'label': '<',
      'type': 'number',
      'value': 'LESS_THAN',
    },
    {
      'label': '<=',
      'type': 'number',
      'value': 'LESS_THAN_INCLUSIVE',
    },
    {
      'append': ':semver',
      'label': 'SemVer >',
      'value': 'GREATER_THAN:semver',
    },
    {
      'append': ':semver',
      'label': 'SemVer >=',
      'value': 'GREATER_THAN_INCLUSIVE:semver',
    },
    {
      'append': ':semver',
      'label': 'SemVer <',
      'value': 'LESS_THAN:semver',
    },
    {
      'append': ':semver',
      'label': 'SemVer <=',
      'value': 'LESS_THAN_INCLUSIVE:semver',
    },
    {
      'label': 'Modulo',
      'value': 'MODULO',
      'valuePlaceholder': 'Divisor|Remainder',
    },
    {
      'label': 'Contains',
      'value': 'CONTAINS',
    },
    {
      'label': 'Does not contain',
      'value': 'NOT_CONTAINS',
    },
    {
      'label': 'In',
      'value': 'IN',
      'valuePlaceholder': 'Value1,Value2',
    },
    {
      'label': 'Matches regex',
      'value': 'REGEX',
    },
    {
      'hideValue': true,
      'label': 'Is set',
      'value': 'IS_SET',
    },
    {
      'hideValue': true,
      'label': 'Is not set',
      'value': 'IS_NOT_SET',
    },
  ],
}

export { defaultFlags }
