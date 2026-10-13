import moment from 'moment'
import { ChangeRequestSummary } from 'common/types/responses'

// The change requests staging this feature's dependencies that are still open
// or scheduled. One that was published or deleted drops out.
export const matchPendingChangeRequests = (
  stagingIds: number[],
  changeRequests: ChangeRequestSummary[],
): ChangeRequestSummary[] =>
  changeRequests.filter((changeRequest) =>
    stagingIds.includes(changeRequest.id),
  )

export const describeStatus = (changeRequest: ChangeRequestSummary) =>
  changeRequest.committed_at && changeRequest.live_from
    ? `Scheduled for ${moment(changeRequest.live_from).format('D MMM, HH:mm')}`
    : 'Awaiting approval'
