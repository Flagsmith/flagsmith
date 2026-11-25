import Constants from 'common/constants'
import { integrationCategories } from 'components/pages/IntegrationsPage'

jest.mock('common/utils/utils', () => ({}))
jest.mock('components/IntegrationList', () => ({}))
jest.mock('common/providers/Permission', () => ({}))
jest.mock('project/api', () => ({}))
jest.mock('common/services/useProject', () => ({}))
jest.mock('components/providers/RouteContext', () => ({}))

describe('Constants.integrationCategoryDescriptions', () => {
  it('provides a non-empty description for every integration category', () => {
    for (const category of integrationCategories) {
      expect(Constants.integrationCategoryDescriptions[category]).toEqual(
        expect.any(String),
      )
      expect(
        Constants.integrationCategoryDescriptions[category].trim().length,
      ).toBeGreaterThan(0)
    }
  })

  it('provides a non-empty description for the All category', () => {
    expect(Constants.integrationCategoryDescriptions.All).toEqual(
      expect.any(String),
    )
    expect(
      Constants.integrationCategoryDescriptions.All.trim().length,
    ).toBeGreaterThan(0)
  })
})
