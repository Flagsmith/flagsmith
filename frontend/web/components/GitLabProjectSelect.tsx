import React, { FC } from 'react'
import type { GitLabProject } from 'common/types/responses'

export type GitLabProjectOption = {
  label: string
  value: number
}

type GitLabProjectSelectProps = {
  projects: GitLabProject[]
  isLoading: boolean
  isFetching: boolean
  isError: boolean
  value: GitLabProjectOption | null
  onChange: (project: GitLabProjectOption) => void
  onInputChange: (search: string) => void
}

const GitLabProjectSelect: FC<GitLabProjectSelectProps> = ({
  isError,
  isFetching,
  isLoading,
  onChange,
  onInputChange,
  projects,
  value,
}) => {
  const options: GitLabProjectOption[] = projects.map((p) => ({
    label: p.path_with_namespace,
    value: p.id,
  }))
  const isBusy = isLoading || isFetching

  return (
    <div style={{ minWidth: 250 }}>
      <Select
        filterOption={(options: any[]) => options}
        className='w-100 react-select'
        size='select-md'
        placeholder={isBusy ? 'Loading...' : 'Select GitLab Project'}
        value={value}
        onChange={(v: GitLabProjectOption) => onChange(v)}
        onInputChange={(e: string) => onInputChange(e)}
        options={options}
        isLoading={isBusy}
        noOptionsMessage={() => {
          if (isBusy) return 'Loading...'
          return isError
            ? 'Failed to load GitLab projects'
            : 'No projects found'
        }}
      />
    </div>
  )
}

export default GitLabProjectSelect
