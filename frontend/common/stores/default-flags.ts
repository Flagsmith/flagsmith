const defaultFlags = {
  integration_data: {
    'amplitude': {
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
      'tags': ['analytics'],
      'title': 'Amplitude',
    },
    'datadog': {
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
      'tags': ['logging'],
      'title': 'Datadog',
    },
    'dynatrace': {
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
      'tags': ['logging'],
      'title': 'Dynatrace',
    },
    'grafana': {
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
      'perEnvironment': false,
      'tags': ['logging'],
      'title': 'Grafana',
    },

    'heap': {
      'description': 'Sends data on what flags served to each identity.',
      'docs': 'https://docs.flagsmith.com/integrations/analytics/heap',
      'fields': [
        {
          'hidden': true,
          'key': 'api_key',
          'label': 'API Key',
        },
      ],
      'image': '/static/images/integrations/heap.svg',
      'perEnvironment': true,
      'tags': ['analytics'],
      'title': 'Heap Analytics',
    },
    'jira': {
      'description': 'View your Flagsmith Flags inside Jira.',
      'docs': 'https://docs.flagsmith.com/integrations/project-management/jira',
      'external': true,
      'image': 'https://docs.flagsmith.com/img/integrations/jira/jira-logo.svg',
      'perEnvironment': false,
      'title': 'Jira',
    },
    'mixpanel': {
      'description': 'Sends data on what flags served to each identity.',
      'docs': 'https://docs.flagsmith.com/integrations/analytics/mixpanel',
      'fields': [
        {
          'hidden': true,
          'key': 'api_key',
          'label': 'Project Token',
        },
      ],
      'image': '/static/images/integrations/mp.svg',
      'perEnvironment': true,
      'tags': ['analytics'],
      'title': 'Mixpanel',
    },
    'new-relic': {
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
      'tags': ['analytics'],
      'title': 'New Relic',
    },
    'rudderstack': {
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
      'tags': ['analytics'],
      'title': 'Rudderstack',
    },
    'segment': {
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
      'tags': ['analytics'],
      'title': 'Segment',
    },
    'slack': {
      'description':
        'Sends messages to Slack when flags are created, updated and removed. Logs are tagged with the environment they came from e.g. production.',
      'docs': 'https://docs.flagsmith.com/integrations/slack',
      'image': '/static/images/integrations/slack.svg',
      'isOauth': true,
      'perEnvironment': true,
      'tags': ['messaging'],
      'title': 'Slack',
    },
    'webhook': {
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
      'tags': ['analytics'],
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
