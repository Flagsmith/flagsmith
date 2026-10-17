import { FC } from 'react'
import IconButton from 'components/base/IconButton'
import cn from 'classnames'
import Chip from 'components/base/Chip'
import Icon from 'components/icons/Icon'
import SegmentsIcon from 'components/icons/SegmentsIcon'
import { CohortSourceType } from 'common/types/responses'
import { colorIconSecondary } from 'common/theme/tokens'
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
  <div className='d-flex flex-column gap-2 mx-0'>
    {segments.map((segment) => (
      <div
        key={segment.id}
        className='audience-segment-row d-flex align-items-center gap-3'
      >
        <SegmentsIcon
          className='flex-shrink-0'
          width={18}
          height={18}
          fill={colorIconSecondary}
        />
        <span
          className='d-flex flex-column flex-1 overflow-hidden gap-1'
          title={segment.name}
        >
          <span className='d-flex align-items-center gap-2 overflow-hidden'>
            <span
              className={cn('fw-semibold text-truncate', {
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
            <span className='text-truncate text-muted'>
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
          <IconButton
            variant='ghost'
            size='medium'
            className='audience-segment-row__remove'
            aria-label={`Remove ${segment.name} from audience`}
            onClick={() => onRemove(segment.id)}
            data-test={`remove-audience-segment-${segment.id}`}
          >
            <Icon width={20} name='trash-2' />
          </IconButton>
        )}
      </div>
    ))}
  </div>
)

export default AudienceSegmentList
