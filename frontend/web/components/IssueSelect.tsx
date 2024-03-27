import React, { FC } from 'react'
import { Issue } from 'common/types/responses'

export type IssueSelectType = {
  disabled?: boolean
  issues: Issue[] | undefined
  onChange: (value: string) => void
}

type IssueValueType = {
  value: string
}

const IssueSelect: FC<IssueSelectType> = ({ disabled, issues, onChange }) => {
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
      />
    </div>
  )
}

export default IssueSelect
