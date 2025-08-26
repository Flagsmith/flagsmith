import { FC } from 'react'
import {
  ChangeRequestSummary,
  PagedResponse,
  User,
} from 'common/types/responses'
import { Link } from 'react-router-dom'
import Icon from './Icon'
import moment from 'moment'
import { IonIcon } from '@ionic/react'
import { timeOutline } from 'ionicons/icons'
import JSONReference from './JSONReference'
import PanelSearch from './PanelSearch'

type ChangeRequestListProps = {
  items: PagedResponse<ChangeRequestSummary> | undefined
  page: number
  setPage: (page: number) => void
  isLoading: boolean
  changeRequests: PagedResponse<ChangeRequestSummary> | undefined
  getLink: (id: string) => string
  users: User[] | undefined
}

const ChangeRequestList: FC<ChangeRequestListProps> = ({
  changeRequests,
  getLink,
  isLoading,
  items,
  page,
  setPage,
  users,
}) => {
  return (
    <PanelSearch
      renderSearchWithNoResults
      className='mt-4 no-pad'
      isLoading={isLoading || !changeRequests}
      items={items?.results}
      paging={items}
      nextPage={() => setPage(page + 1)}
      prevPage={() => setPage(page - 1)} // ✅ fixed bug: was page+1 in both
      goToPage={setPage}
      renderFooter={() => (
        <JSONReference
          className='mt-4 ml-3'
          title='Change Requests'
          json={items?.results}
        />
      )}
      renderRow={({
        created_at,
        description,
        id,
        live_from,
        title,
        user: _user,
      }: ChangeRequestSummary) => {
        const user = users?.find((v) => v.id === _user)
        const isScheduled =
          new Date(`${live_from}`).valueOf() > new Date().valueOf()

        return (
          <Link to={getLink(`${id}`)} className='flex-row list-item clickable'>
            <Flex className='table-column px-3'>
              <div className='font-weight-medium'>
                {title}
                {isScheduled && (
                  <span className='ml-1 mr-4 ion'>
                    <IonIcon icon={timeOutline} />
                  </span>
                )}
              </div>
              <div className='list-item-subtitle mt-1'>
                Created {moment(created_at).format('Do MMM YYYY HH:mma')}
                {!!user && (
                  <>
                    {' '}
                    by {user.first_name || 'Unknown'} {user.last_name || 'user'}
                  </>
                )}
                {description ? ` - ${description}` : ''}
              </div>
            </Flex>
            <div className='table-column'>
              <Icon name='chevron-right' fill='#9DA4AE' width={20} />
            </div>
          </Link>
        )
      }}
    />
  )
}

export default ChangeRequestList
