import React, { FC } from 'react'
import { Res, Segment } from 'common/types/responses'
import { useGetSegmentsQuery } from 'common/services/useSegment'
import useInfiniteScroll from 'common/useInfiniteScroll'
import { Req } from 'common/types/requests' // we need this to make JSX compile
import { components } from 'react-select'
import { SelectProps } from '@material-ui/core/Select/Select'
import Utils from 'common/utils/utils'
import Button from './base/forms/Button'

type SegmentSelectType = {
  disabled: boolean
  projectId: string
  'data-test'?: string
  placeholder?: string
  value: SelectProps['value']
  onChange: SelectProps['onChange']
  filter?: (segments: Segment) => Segment[]
}

const SegmentSelect: FC<SegmentSelectType> = ({
  filter,
  projectId,
  ...rest
}) => {
  const { data, isLoading, loadMore, searchItems } = useInfiniteScroll<
    Req['getSegments'],
    Res['segments']
  >(useGetSegmentsQuery, { page_size: 100, projectId })

  const options = (
    data
      ? filter
        ? (data.results.filter(filter) as Res['segments']['results'])
        : data.results
      : []
  ).map(({ feature, id: value, name: label }) => ({ feature, label, value }))

  return (
    //@ts-ignore
    <Select
      data-test={rest['data-test']}
      placeholder={rest.placeholder}
      value={rest.value}
      isDisabled={rest.disabled}
      onChange={rest.onChange}
      onInputChange={(e: any) => {
        searchItems(Utils.safeParseEventValue(e))
      }}
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
          </div>
        ),
      }}
      options={options}
      styles={{
        control: (base: any) => ({
          ...base,
          '&:hover': { borderColor: '$bt-brand-secondary' },
          border: '1px solid $bt-brand-secondary',
        }),
      }}
    />
  )
}

export default SegmentSelect
