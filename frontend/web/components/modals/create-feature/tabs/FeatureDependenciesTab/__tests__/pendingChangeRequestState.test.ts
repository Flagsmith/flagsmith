import { ChangeRequestSummary } from 'common/types/responses'
import { describeStatus } from 'components/modals/create-feature/tabs/FeatureDependenciesTab/pendingChangeRequestState'

const changeRequest = (
  id: number,
  fields: Partial<ChangeRequestSummary> = {},
) =>
  ({
    committed_at: null,
    id,
    live_from: null,
    ...fields,
  } as ChangeRequestSummary)

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
