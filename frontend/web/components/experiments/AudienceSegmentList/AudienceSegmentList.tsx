import { FC } from 'react'
import cn from 'classnames'
import Chip from 'components/base/Chip'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import SegmentsIcon from 'components/icons/SegmentsIcon'
import { CohortSourceType } from 'common/types/responses'
import './AudienceSegmentList.scss'

export type AudienceSegmentItem = {
  id: number
  name: string
  cohortSourceType?: CohortSourceType | null
  description?: string
  membershipCount?: number
  deleted?: boolean
}

type AudienceSegmentListProps = {
  segments: AudienceSegmentItem[]
  onRemove?: (id: number) => void
}

const AudienceSegmentList: FC<AudienceSegmentListProps> = ({
  onRemove,
  segments,
}) => (
  <div className='audience-segment-list'>
    {segments.map((segment) => (
      <div key={segment.id} className='audience-segment-list__row'>
        <SegmentsIcon
          className='audience-segment-list__icon'
          width={18}
          height={18}
          fill='#656D7B'
        />
        <span className='audience-segment-list__body' title={segment.name}>
          <span className='audience-segment-list__title'>
            <span
              className={cn('audience-segment-list__name-text', {
                'text-muted': segment.deleted,
              })}
            >
              {segment.name}
              {segment.deleted && ' (deleted)'}
            </span>
            {!!segment.cohortSourceType && (
              <Chip size='xs' variant='accent'>
                {segment.cohortSourceType.toUpperCase()}
              </Chip>
            )}
          </span>
          {!!segment.description && (
            <span className='audience-segment-list__description text-muted'>
              {segment.description}
            </span>
          )}
        </span>
        {typeof segment.membershipCount === 'number' && (
          <span className='text-muted text-nowrap fs-caption'>
            {segment.membershipCount.toLocaleString()}{' '}
            {segment.membershipCount === 1 ? 'identity' : 'identities'}
          </span>
        )}
        {onRemove && (
          <Button
            className='btn btn-with-icon'
            type='button'
            aria-label={`Remove ${segment.name} from audience`}
            onClick={() => onRemove(segment.id)}
            data-test={`remove-audience-segment-${segment.id}`}
          >
            <Icon name='trash-2' width={20} fill='#656D7B' />
          </Button>
        )}
      </div>
    ))}
  </div>
)

export default AudienceSegmentList
