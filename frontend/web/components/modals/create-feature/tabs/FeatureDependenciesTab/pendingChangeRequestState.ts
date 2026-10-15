import moment from 'moment'
import { ChangeRequestSummary } from 'common/types/responses'

// Approved, and waiting only for its live date.
export const isScheduled = (changeRequest: ChangeRequestSummary) =>
  !!changeRequest.committed_at && !!changeRequest.live_from

export const describeStatus = (changeRequest: ChangeRequestSummary) =>
  isScheduled(changeRequest)
    ? `Scheduled for ${moment(changeRequest.live_from).format('D MMM, HH:mm')}`
    : 'Awaiting approval'
