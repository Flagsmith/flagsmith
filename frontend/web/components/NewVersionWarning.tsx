import { FC, useMemo } from 'react'
import { useGetFeatureVersionsQuery } from 'common/services/useFeatureVersion'
import moment from 'moment'
import ErrorMessage from './ErrorMessage' // we need this to make JSX compile

type NewVersionWarningType = {
  date: string
  featureId: number
  environmentId: string
}

const NewVersionWarning: FC<NewVersionWarningType> = ({
  date,
  environmentId,
  featureId,
}) => {
  const { data } = useGetFeatureVersionsQuery(
    { environmentId, featureId, is_live: true, page_size: 1 },
    { refetchOnMountOrArgChange: true, skip: !environmentId || !featureId },
  )
  const compareDate = data?.results?.[0]?.live_from
  const isNewVersion = useMemo(() => {
    if (compareDate && date) {
      if (moment(compareDate).valueOf() > moment(date).valueOf()) {
        return true
      }
    }
    return false
  }, [compareDate, date])
  return isNewVersion ? (
    <div className='mt-4'>
      <ErrorMessage
        error={`A new change request has been published for this feature since this one was created, please check that the change request is as you'd expect.`}
      />
    </div>
  ) : null
}

export default NewVersionWarning
