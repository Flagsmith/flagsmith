import React, { FC } from 'react'
import { Res, Segment } from 'common/types/responses'
import { useGetSegmentsQuery } from 'common/services/useSegment'
import useInfiniteScroll from 'common/useInfiniteScroll'
import { Req } from 'common/types/requests'
import { components } from 'react-select'
import Utils from 'common/utils/utils'
import Button from './base/forms/Button'
import Chip from './base/Chip'

type SegmentSelectType = {
  disabled: boolean
  projectId: string
  'data-test'?: string
  placeholder?: string
  className?: string
  value: number | string | undefined
  onChange: (value: any) => void
  filter?: (segments: Segment) => Segment[]
}

const SegmentSelect: FC<SegmentSelectType> = ({
  className,
  filter,
  projectId,
  ...rest
}) => {
  const { data, isLoading, loadMore, searchItems } = useInfiniteScroll<
    Req['getSegments'],
    Res['segments']
  >(useGetSegmentsQuery, { page_size: 100, projectId })

  let filteredResults: Res['segments']['results'] = []
  if (data) {
    // A cohort awaiting deletion is already gone from the user's point of view.
    filteredResults = data.results.filter(
      (segment) => !segment.cohort?.deletion_requested_at,
    )
    if (filter) {
      filteredResults = filteredResults.filter(
        filter,
      ) as Res['segments']['results']
    }
  }
  const options = filteredResults.map(
    ({ cohort, feature, id: value, name: label }) => ({
      cohort,
      feature,
      label,
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
        Option: ({ children, data, innerProps, innerRef }: any) => (
          <div ref={innerRef} {...innerProps} className='react-select__option'>
            {children}
            {!!data.feature && (
              <div className='unread ml-2 px-2'>Feature-Specific</div>
            )}
            {!!data.cohort && (
              <Chip className='ml-2' size='xs' variant='accent'>
                {data.cohort.source_type.toUpperCase()}
              </Chip>
            )}
          </div>
        ),
      }}
      options={options}
    />
  )
}

export default SegmentSelect
