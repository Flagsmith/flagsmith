import { ChangeRequestSummary } from 'common/types/responses'
import { describeStatus } from 'components/modals/create-feature/tabs/FeatureDependenciesTab/pendingChangeRequestState'

const changeRequest = (
  id: number,
  fields: Partial<ChangeRequestSummary> = {},
): ChangeRequestSummary => ({
  committed_at: null,
  committed_by: null,
  created_at: '2026-10-13T09:00:00Z',
  deleted_at: null,
  description: '',
  id,
  live_from: null,
  readOnly: false,
  title: 'Add prerequisites',
  updated_at: '2026-10-13T09:00:00Z',
  user: 1,
  ...fields,
})

describe('describeStatus', () => {
  it('reads an approved change request with a live date as scheduled', () => {
    expect(
      describeStatus(
        changeRequest(1, {
          committed_at: '2026-10-13T10:00:00Z',
          live_from: '2026-10-20T09:30:00Z',
        }),
      ),
    ).toMatch(/^Scheduled for 20 Oct, /)
  })

  it('reads anything else as awaiting approval', () => {
    expect(describeStatus(changeRequest(1))).toBe('Awaiting approval')
  })
})
