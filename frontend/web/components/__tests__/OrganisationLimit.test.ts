import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import Constants from 'common/constants'
import { useGetOrganisationUsageQuery } from 'common/services/useOrganisationUsage'
import { useGetSubscriptionMetadataQuery } from 'common/services/useSubscriptionMetadata'
import Utils from 'common/utils/utils'
import OrganisationLimit from 'components/OrganisationLimit'

let capturedButtonOnClick: (() => void) | undefined

jest.mock('common/services/useOrganisationUsage', () => ({
  useGetOrganisationUsageQuery: jest.fn(),
}))

jest.mock('common/services/useSubscriptionMetadata', () => ({
  useGetSubscriptionMetadataQuery: jest.fn(),
}))

jest.mock('common/utils/utils', () => ({
  __esModule: true,
  default: {
    calculateRemainingLimitsPercentage: jest.fn(),
    getFlagsmithHasFeature: jest.fn(),
    getPlanName: jest.fn(),
  },
}))

jest.mock('common/constants', () => ({
  __esModule: true,
  default: {
    getUpgradeUrl: jest.fn(),
  },
}))

jest.mock('components/icons/Icon', () => ({
  __esModule: true,
  default: () => null,
}))

jest.mock('components/WarningMessage', () => ({
  __esModule: true,
  default: () => null,
}))

jest.mock('components/base/forms/Button', () => ({
  Button: ({
    children,
    onClick,
  }: {
    children: React.ReactNode
    onClick?: () => void
  }) => {
    capturedButtonOnClick = onClick
    return React.createElement('button', { type: 'button' }, children)
  },
}))

const mockGetUsage = useGetOrganisationUsageQuery as jest.Mock
const mockGetSubscription = useGetSubscriptionMetadataQuery as jest.Mock
const mockCalculatePercentage =
  Utils.calculateRemainingLimitsPercentage as jest.Mock
const mockHasFeature = Utils.getFlagsmithHasFeature as jest.Mock
const mockGetPlanName = Utils.getPlanName as jest.Mock
const mockGetUpgradeUrl = Constants.getUpgradeUrl as jest.Mock

const globalWithRow = global as unknown as {
  Row?: React.FC<{ children?: React.ReactNode }>
  document?: { location: { replace: jest.Mock } }
}

const originalRow = globalWithRow.Row
const originalDocument = globalWithRow.document

beforeAll(() => {
  globalWithRow.Row = ({ children }) =>
    React.createElement('div', null, children)
})

afterAll(() => {
  globalWithRow.Row = originalRow
  globalWithRow.document = originalDocument
})

beforeEach(() => {
  capturedButtonOnClick = undefined
  mockGetUsage.mockReturnValue({ data: { totals: { total: 60000 } } })
  mockGetSubscription.mockReturnValue({ data: { max_api_calls: 50000 } })
  mockCalculatePercentage.mockReturnValue({ percentage: 120 })
  mockHasFeature.mockReturnValue(true)
  mockGetPlanName.mockImplementation((plan: string) => plan)
  mockGetUpgradeUrl.mockReturnValue('/organisation-settings?tab=billing')
})

describe('OrganisationLimit', () => {
  it('shows the upgrade prompt and button to admins on the Free plan', () => {
    const html = renderToStaticMarkup(
      React.createElement(OrganisationLimit, {
        id: '1',
        isAdmin: true,
        organisationPlan: 'Free',
      }),
    )

    expect(html).toContain('Your organisation has exceeded its API usage quota')
    expect(html).toContain(
      'Please upgrade your plan to continue receiving service.',
    )
    expect(html).toContain('Upgrade plan')
  })

  it('keeps the banner for non-admins on the Free plan without the upgrade button', () => {
    const html = renderToStaticMarkup(
      React.createElement(OrganisationLimit, {
        id: '1',
        isAdmin: false,
        organisationPlan: 'Free',
      }),
    )

    expect(html).toContain('Your organisation has exceeded its API usage quota')
    expect(html).toContain(
      'Ask an organisation admin to upgrade to continue receiving service.',
    )
    expect(html).not.toContain('Please upgrade your plan')
    expect(html).not.toContain('Upgrade plan')
  })

  it('hides the upgrade button for non-admins on paid plans while keeping overage copy', () => {
    const html = renderToStaticMarkup(
      React.createElement(OrganisationLimit, {
        id: '1',
        isAdmin: false,
        organisationPlan: 'Start-Up',
      }),
    )

    expect(html).toContain('Your organisation has exceeded its API usage quota')
    expect(html).toContain('Automated billing for the overages may apply.')
    expect(html).not.toContain('Upgrade plan')
  })

  it('navigates to Constants.getUpgradeUrl("usage") when an admin clicks Upgrade plan', () => {
    const replace = jest.fn()
    globalWithRow.document = { location: { replace } }

    renderToStaticMarkup(
      React.createElement(OrganisationLimit, {
        id: '1',
        isAdmin: true,
        organisationPlan: 'Free',
      }),
    )

    expect(capturedButtonOnClick).toBeDefined()
    capturedButtonOnClick?.()

    expect(mockGetUpgradeUrl).toHaveBeenCalledWith('usage')
    expect(replace).toHaveBeenCalledWith('/organisation-settings?tab=billing')
  })
})
