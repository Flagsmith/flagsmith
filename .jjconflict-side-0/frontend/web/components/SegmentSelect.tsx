import React, { FC } from 'react'
import { Res, Segment, SegmentMembership } from 'common/types/responses'
import { useGetSegmentsQuery } from 'common/services/useSegment'
import useInfiniteScroll from 'common/useInfiniteScroll'
import { Req } from 'common/types/requests'
import { components } from 'react-select'
import Utils from 'common/utils/utils'
import Button from './base/forms/Button'
import Chip from './base/Chip'

type SegmentSelectType = {
  disabled?: boolean
  projectId: string
  'data-test'?: string
  placeholder?: string
  className?: string
  value: number | string | undefined
  onChange: (value: any) => void
  filter?: (segment: Segment) => boolean
  // When set, options display the segment's membership count for this
  // environment (database id, not api key), when the backend has computed one.
  membershipCountEnvironmentId?: number
}

const SegmentSelect: FC<SegmentSelectType> = ({
  className,
  filter,
  membershipCountEnvironmentId,
  projectId,
  ...rest
}) => {
  const { data, isLoading, loadMore, searchItems } = useInfiniteScroll<
    Req['getSegments'],
    Res['segments']
  >(useGetSegmentsQuery, { page_size: 100, projectId: Number(projectId) })

  let filteredResults: Res['segments']['results'] = []
  if (data) {
    // A cohort awaiting deletion is already gone from the user's point of view.
    filteredResults = data.results.filter(
      (segment) => !segment.cohort?.deletion_requested_at,
    )
    if (filter) {
      filteredResults = filteredResults.filter(filter)
    }
  }
  const options = filteredResults.map(
    ({
      cohort,
      description,
      feature,
      id: value,
      membership_counts,
      name: label,
    }) => ({
      cohort,
      description,
      feature,
      label,
      membership_counts,
      value,
    }),
  )

  return (
    //@ts-ignore
    <Select
      data-test={rest['data-test']}
      placeholder={rest.placeholder}
      value={rest.value ? options.find((v) => v.value === rest.value) : null}
      isDisabled={rest.disabled}
      onChange={rest.onChange}
      onInputChange={(e: any) => {
        searchItems(Utils.safeParseEventValue(e))
      }}
      className={className}
      components={{
        Menu: ({ ...props }: any) => {
          return (
            <components.Menu {...props}>
              <React.Fragment>
                {props.children}
                {!!data?.next && (
                  <div className='text-center mb-4'>
                    <Button
                      theme='outline'
                      onClick={() => {
                        loadMore()
                      }}
                      disabled={isLoading}
                    >
                      Load More
                    </Button>
                  </div>
                )}
              </React.Fragment>
            </components.Menu>
          )
        },
        Option: ({ children, data, innerProps, innerRef }: any) => {
          const membershipCount =
            membershipCountEnvironmentId === undefined
              ? undefined
              : data.membership_counts?.find(
                  (membership: SegmentMembership) =>
                    membership.environment === membershipCountEnvironmentId,
                )?.count
          return (
            <div
              ref={innerRef}
              {...innerProps}
              className='react-select__option d-flex align-items-center'
            >
              {children}
              {!!data.feature && (
                <div className='unread ml-2 px-2'>Feature-Specific</div>
              )}
              {!!data.cohort && (
                <Chip className='ml-2' size='xs' variant='accent'>
                  {data.cohort.source_type.toUpperCase()}
                </Chip>
              )}
              {typeof membershipCount === 'number' && (
                <span className='ml-auto text-muted fs-caption text-nowrap'>
                  {membershipCount.toLocaleString()}{' '}
                  {membershipCount === 1 ? 'identity' : 'identities'}
                </span>
              )}
            </div>
          )
        },
      }}
      options={options}
    />
  )
}

export default SegmentSelect
