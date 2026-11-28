import AccountStore from 'common/stores/account-store'
import {
  getCurrentOrganisation,
  isOrganisationAdmin,
} from 'common/hooks/useCurrentOrganisation'
import { getCurrentUser } from 'common/hooks/useCurrentUser'
import { AccountModel, Organisation } from 'common/types/responses'

jest.mock('common/stores/account-store', () => ({
  getOrganisation: jest.fn(),
  getUser: jest.fn(),
}))

const store = jest.mocked(AccountStore)

const organisation = (role: Organisation['role']): Organisation => ({
  api_limit_grace_period_used: false,
  api_limit_restriction_enabled: false,
  block_access_to_admin: false,
  created_date: '2026-01-01T00:00:00Z',
  id: 1,
  name: 'Acme',
  num_seats: 1,
  overage_billing_eligible: false,
  persist_trait_data: true,
  restrict_project_create_to_admin: false,
  role,
  stop_serving_flags: false,
  subscription: {
    cancellation_date: null,
    current_billing_period: null,
    customer_id: '',
    has_active_billing_periods: false,
    id: 1,
    max_api_calls: 50000,
    max_seats: 1,
    notes: null,
    payment_method: null,
    plan: null,
    subscription_date: '2026-01-01T00:00:00Z',
    subscription_id: null,
    uuid: 'subscription-uuid',
  },
  webhook_notification_email: null,
})

describe('getCurrentOrganisation', () => {
  it.each([
    ['the organisation', organisation('ADMIN'), organisation('ADMIN')],
    ['undefined for null', null, undefined],
    ['undefined for undefined', undefined, undefined],
  ])('returns %s', (_, stored, expected) => {
    store.getOrganisation.mockReturnValue(stored)
    expect(getCurrentOrganisation()).toEqual(expected)
  })
})

describe('isOrganisationAdmin', () => {
  it.each([
    ['an admin', organisation('ADMIN'), true],
    ['a user', organisation('USER'), false],
    ['no organisation', undefined, false],
  ])('for %s returns %s', (_, value, expected) => {
    expect(isOrganisationAdmin(value)).toBe(expected)
  })
})

describe('getCurrentUser', () => {
  const user: AccountModel = {
    auth_type: 'EMAIL',
    date_joined: '2026-01-01T00:00:00Z',
    email: 'ada@example.com',
    first_name: 'Ada',
    id: 7,
    is_superuser: false,
    last_name: 'Lovelace',
    organisations: [],
    pylon_email_signature: '',
    sign_up_type: 'NO_INVITE',
    uuid: 'user-uuid',
  }
  it.each([
    ['the user', user, user],
    ['undefined for null', null, undefined],
  ])('returns %s', (_, stored, expected) => {
    store.getUser.mockReturnValue(stored)
    expect(getCurrentUser()).toEqual(expected)
  })
})
