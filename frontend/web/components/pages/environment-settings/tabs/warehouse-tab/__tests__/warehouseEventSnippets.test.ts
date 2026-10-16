import {
  EVENTS_URL_PLACEHOLDER,
  getWarehouseEventSnippets,
} from 'components/pages/environment-settings/tabs/warehouse-tab/warehouseEventSnippets'

const selfHosted = {
  apiUrl: 'https://flagsmith.example.com/api/v1/',
  eventsUrl: EVENTS_URL_PLACEHOLDER,
}

describe('getWarehouseEventSnippets', () => {
  it('covers the SDKs documented for experimentation', () => {
    expect(Object.keys(getWarehouseEventSnippets()).sort()).toEqual([
      'Flutter',
      'Go',
      'Java',
      'JavaScript',
      'Node JS',
      'Python',
      'React',
    ])
  })

  it.each([
    ['Flutter', 'flagsmith 6.2.0+', 'await flagsmith.flushEvents();'],
    ['Go', 'flagsmith-go-client/v5 5.3.0+', 'client.FlushEvents(flushCtx)'],
    ['Java', 'flagsmith-java-client 8.2.0+', 'flagsmith.close();'],
    ['JavaScript', '@flagsmith/flagsmith 12.4.0+', 'flagsmith.flushEvents();'],
    ['Node JS', '@flagsmith/nodejs 9.1.0+', 'await flagsmith.close();'],
    ['Python', 'flagsmith 6.3.0+', 'max_buffer_items=1'],
    ['React', '@flagsmith/flagsmith 12.4.0+', 'useExperiment('],
  ])(
    '%s states its minimum version and the docs guidance',
    (language, version, guidance) => {
      const snippet = getWarehouseEventSnippets()[language]
      expect(snippet).toContain(`Requires ${version}`)
      expect(snippet).toContain(guidance)
    },
  )

  it('leaves the SDK defaults (Flagsmith Cloud) in place on SaaS', () => {
    Object.values(getWarehouseEventSnippets()).forEach((snippet) => {
      expect(snippet).not.toMatch(
        /\bapi:|apiUrl|api_url|baseU(RI|ri)|BaseURL|events(Api)?U(RI|rl|ri)|events_api_url/,
      )
    })
  })

  it.each([
    ['Flutter', "baseURI: '", "eventsURI: '"],
    ['Go', 'WithBaseURL("', 'WithEventsBaseURL("'],
    ['Java', '.baseUri("', '.eventsUri("'],
    ['JavaScript', "api: '", "eventsApiUrl: '"],
    ['Node JS', "apiUrl: '", "eventsApiUrl: '"],
    ['Python', 'api_url="', 'events_api_url="'],
    ['React', "api: '", "eventsApiUrl: '"],
  ])(
    '%s points at the self-hosted API and event ingestion service',
    (language, apiKey, eventsKey) => {
      const snippet = getWarehouseEventSnippets(selfHosted)[language]
      expect(snippet).toContain(`${apiKey}${selfHosted.apiUrl}`)
      expect(snippet).toContain(`${eventsKey}${selfHosted.eventsUrl}`)
    },
  )
})
