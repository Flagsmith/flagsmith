import React, { FC, useState } from 'react'
import { components } from 'react-select'
import { PullRequest } from 'common/types/responses'
import Button from './base/forms/Button'
import Utils from 'common/utils/utils'

export type PullRequestsSelectType = {
  disabled?: boolean
  isFetching: boolean
  isLoading: boolean
  pullRequest: PullRequest[]
  onChange: (value: string) => void
  loadMore: () => void
  nextPage?: string
  searchItems: (search: string) => void
}

type PullRequestValueType = {
  value: string
  label: string
}

const PullRequestsSelect: FC<PullRequestsSelectType> = ({
  disabled,
  isFetching,
  isLoading,
  loadMore,
  nextPage,
  onChange,
  pullRequest,
  searchItems,
}) => {
  const [searchTimer, setSearchTimer] = useState<NodeJS.Timeout | null>(null)

  const handleInputChange = (e: any) => {
    const value = Utils.safeParseEventValue(e)

    if (searchTimer) {
      clearTimeout(searchTimer)
    }

    setSearchTimer(
      setTimeout(() => {
        searchItems(value)
      }, 500),
    )
  }

  return (
    <div style={{ width: '300px' }}>
      <Select
        size='select-md'
        placeholder={'Select Your PR'}
        onChange={(v: PullRequestValueType) => {
          onChange(v?.value)
        }}
        disabled={disabled}
        options={pullRequest?.map((p: PullRequest) => {
          return {
            label: `${p.title} #${p.number}`,
            value: p.html_url,
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
          handleInputChange(e)
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

export default PullRequestsSelect
