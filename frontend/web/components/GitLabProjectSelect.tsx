import React, { FC } from 'react'
import type { GitLabProject } from 'common/types/responses'

type GitLabProjectSelectProps = {
  projects: GitLabProject[]
  isLoading: boolean
  isDisabled: boolean
  value: number | null
  onChange: (id: number) => void
}

const GitLabProjectSelect: FC<GitLabProjectSelectProps> = ({
  isDisabled,
  isLoading,
  onChange,
  projects,
  value,
}) => {
  const options = projects.map((p) => ({
    label: p.path_with_namespace,
    value: p.id,
  }))

  return (
    <div style={{ minWidth: 250 }}>
      <Select
        className='w-100 react-select'
        size='select-md'
        placeholder={isLoading ? 'Loading...' : 'Select GitLab Project'}
        value={options.find((o) => o.value === value) ?? null}
        onChange={(v: { value: number }) => onChange(v.value)}
        options={options}
        isLoading={isLoading}
        isDisabled={isDisabled}
      />
    </div>
  )
}

export default GitLabProjectSelect
