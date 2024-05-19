import React, { FC } from 'react'
import { PullRequest } from 'common/types/responses'

export type PullRequestsSelectType = {
  disabled?: boolean
  pullRequest: PullRequest[] | undefined
  onChange: (value: string) => void
  isLoading: boolean
}

type PullRequestValueType = {
  value: string
}

const PullRequestsSelect: FC<PullRequestsSelectType> = ({
  disabled,
  isLoading,
  onChange,
  pullRequest,
}) => {
  return (
    <div style={{ width: '300px' }}>
      <Select
        size='select-md'
        placeholder={'Select Your PR'}
        onChange={(v: PullRequestValueType) => onChange(v?.value)}
        disabled={disabled}
        options={pullRequest?.map((p: PullRequest) => {
          return {
            label: `${p.title} #${p.number}`,
            value: p.html_url,
          }
        })}
        noOptionsMessage={() => (isLoading ? 'Loading...' : 'No PRs found')}
      />
    </div>
  )
}

export default PullRequestsSelect
