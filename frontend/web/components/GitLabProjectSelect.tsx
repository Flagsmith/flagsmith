import React, { FC } from 'react'
import { useGetGitLabProjectsQuery } from 'common/services/useGitlab'

type GitLabProjectSelectProps = {
  projectId: number
  value: number | null
  onChange: (id: number) => void
}

const GitLabProjectSelect: FC<GitLabProjectSelectProps> = ({
  onChange,
  projectId,
  value,
}) => {
  const { data, isError, isLoading } = useGetGitLabProjectsQuery({
    page: 1,
    page_size: 100,
    project_id: projectId,
  })

  return (
    <div style={{ minWidth: 250 }}>
      <Select
        className='w-100 react-select'
        size='select-md'
        placeholder={
          isLoading
            ? 'Loading...'
            : isError
              ? 'Failed to load projects'
              : 'Select GitLab Project'
        }
        value={
          data?.results
            ? data.results
                .map((p) => ({
                  label: p.path_with_namespace,
                  value: p.id,
                }))
                .find((o) => o.value === value)
            : null
        }
        onChange={(v: { value: number }) => onChange(v.value)}
        options={
          data?.results?.map((p) => ({
            label: p.path_with_namespace,
            value: p.id,
          })) ?? []
        }
        isLoading={isLoading}
        isDisabled={isError}
      />
    </div>
  )
}

export default GitLabProjectSelect
