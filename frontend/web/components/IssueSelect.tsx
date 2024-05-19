import React, { FC } from 'react'
import { components } from 'react-select'
import { Issue } from 'common/types/responses'
import Button from './base/forms/Button'
import Utils from 'common/utils/utils'

export type IssueSelectType = {
  disabled?: boolean
  isFetching: boolean
  isLoading: boolean
  issues?: Issue[]
  loadMore: () => void
  nextPage?: string
  onChange: (value: string) => void
  searchItems: (search: string) => void
}

type IssueValueType = {
  value: string
}

const IssueSelect: FC<IssueSelectType> = ({
  disabled,
  isFetching,
  isLoading,
  issues,
  loadMore,
  nextPage,
  onChange,
  searchItems,
}) => {
  return (
    <div style={{ width: '300px' }}>
      <Select
        size='select-md'
        placeholder={'Select Your Issue'}
        onChange={(v: IssueValueType) => onChange(v?.value)}
        disabled={disabled}
        options={issues?.map((i: Issue) => {
          return {
            label: `${i.title} #${i.number}`,
            status: i.state,
            value: i.html_url,
          }
        })}
        noOptionsMessage={() =>
          isLoading
            ? 'Loading...'
            : isFetching
            ? 'Refreshing data ...'
            : 'No issues found'
        }
        onInputChange={(e: any) => {
          searchItems(Utils.safeParseEventValue(e))
        }}
        components={{
          Menu: ({ ...props }: any) => {
            return (
              <components.Menu {...props}>
                <React.Fragment>
                  {props.children}
                  {!!nextPage && (
                    <div className='text-center mb-4'>
                      <Button
                        theme='outline'
                        onClick={() => {
                          loadMore()
                        }}
                        disabled={isLoading || isFetching}
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
            <div
              ref={innerRef}
              {...innerProps}
              className='react-select__option'
            >
              {children}
              {!!data.feature && (
                <div className='unread ml-2 px-2'>Feature-Specific</div>
              )}
            </div>
          ),
        }}
      />
    </div>
  )
}

export default IssueSelect
