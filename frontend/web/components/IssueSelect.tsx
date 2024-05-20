import React, { FC, useState, useEffect } from 'react'
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
  resetValue: boolean
}

type IssueValueType = {
  value: string
  label: string
}

const IssueSelect: FC<IssueSelectType> = ({
  disabled,
  isFetching,
  isLoading,
  issues,
  loadMore,
  nextPage,
  onChange,
  resetValue,
  searchItems,
}) => {
  const [value, setValue] = useState<string | null>('')
  const [searchTimer, setSearchTimer] = useState<NodeJS.Timeout | null>(null)
  useEffect(() => {
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
        placeholder={'Select Your Issue'}
        onChange={(v: IssueValueType) => {
          onChange(v?.value)
          if (v?.label) {
            setValue(v?.label)
          }
        }}
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

export default IssueSelect
