import { PagedRequest } from './types/requests'
import { PagedResponse } from './types/responses'

export default function (req: PagedRequest<any>, res: PagedResponse<any>) {
  return {
    ...res,
    currentPage: req.page || 1,
    pageSize: req.page_size,
  }
}
