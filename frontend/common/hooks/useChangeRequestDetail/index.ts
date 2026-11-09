import Utils from 'common/utils/utils'
import { useFluxChangeRequestDetail } from './useFluxChangeRequestDetail'
import { useRtkChangeRequestDetail } from './useRtkChangeRequestDetail'
import type { ChangeRequestDetail, ChangeRequestDetailParams } from './types'

export type * from './types'

export const useChangeRequestDetail = (
  params: Omit<ChangeRequestDetailParams, 'enabled'>,
): ChangeRequestDetail => {
  const rtkEnabled = Utils.getFlagsmithHasFeature('change_requests_rtk')
  const flux = useFluxChangeRequestDetail({ ...params, enabled: !rtkEnabled })
  const rtk = useRtkChangeRequestDetail({ ...params, enabled: rtkEnabled })
  return rtkEnabled ? rtk : flux
}
