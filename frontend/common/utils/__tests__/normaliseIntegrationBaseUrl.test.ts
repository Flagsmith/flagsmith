import { normaliseIntegrationBaseUrl } from 'common/utils/normaliseIntegrationBaseUrl'

describe('normaliseIntegrationBaseUrl', () => {
  it('appends a trailing slash to a custom New Relic base_url', () => {
    const result = normaliseIntegrationBaseUrl('new-relic', {
      api_key: 'key',
      base_url: 'https://custom.newrelic.example.com',
    })
    expect(result.base_url).toBe('https://custom.newrelic.example.com/')
  })

  it('leaves a slash-terminated New Relic base_url unchanged', () => {
    const formData = { base_url: 'https://api.newrelic.com/' }
    expect(normaliseIntegrationBaseUrl('new-relic', formData)).toBe(formData)
  })

  it('leaves an empty New Relic base_url unchanged', () => {
    const formData = { base_url: '' }
    expect(normaliseIntegrationBaseUrl('new-relic', formData)).toBe(formData)
  })

  it('leaves other integrations unchanged', () => {
    const formData = { base_url: 'https://api.datadoghq.com' }
    expect(normaliseIntegrationBaseUrl('datadog', formData)).toBe(formData)
  })

  it('does not mutate the original form data', () => {
    const formData = { base_url: 'https://custom.example.com' }
    normaliseIntegrationBaseUrl('new-relic', formData)
    expect(formData.base_url).toBe('https://custom.example.com')
  })
})
