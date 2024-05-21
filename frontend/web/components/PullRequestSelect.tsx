import React, { FC, useEffect, useState } from 'react'
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
  resetValue: boolean
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
  resetValue,
  searchItems,
}) => {
  const [value, setValue] = useState<string | null>('')
  const [searchTimer, setSearchTimer] = useState<NodeJS.Timeout | null>(null)
  useEffect(() => {
    console.log('DEBUG: resetValue', resetValue)
    resetValue && setValue('')
  }, [resetValue])

  const handleInputChange = (e: any) => {
    const value = Utils.safeParseEventValue(e)
    setValue(value)

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
        value={value ? { label: value, value: value } : null}
        size='select-md'
        placeholder={'Select Your PR'}
        onChange={(v: PullRequestValueType) => {
          onChange(v?.value)
          if (v?.label) {
            setValue(v?.label)
          }
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
            : 'No Pull request found'
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
            </div>
          ),
        }}
      />
    </div>
  )
}

export default PullRequestsSelect
