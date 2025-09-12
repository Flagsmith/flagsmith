import { FC, useEffect, useMemo } from 'react'
import { useGetProjectsQuery } from 'common/services/useProject'

export type ProjectFilterType = {
  organisationId: number
  value?: string
  onChange: (id: string, name: string) => void
  showAll?: boolean
}

const ProjectFilter: FC<ProjectFilterType> = ({
  onChange,
  organisationId,
  showAll,
  value,
}) => {
  const { data } = useGetProjectsQuery(
    { organisationId: `${organisationId}` },
    { skip: isNaN(organisationId) },
  )

  useEffect(() => {
    if (data && data.length === 1) {
      const project = data[0]
      onChange(`${project.id}`, project.name)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data])

  const foundValue = useMemo(
    () => data?.find((project) => `${project.id}` === value),
    [value, data],
  )
  return (
    <Select
      value={
        foundValue
          ? { label: foundValue.name, value: `${foundValue.id}` }
          : { label: showAll ? 'All Projects' : 'Select a Project', value: '' }
      }
      options={(showAll ? [{ label: 'All Projects', value: '' }] : []).concat(
        (data || [])?.map((v) => ({ label: v.name, value: `${v.id}` })),
      )}
      onChange={(value: { value: string; label: string }) =>
        onChange(value.value || '', value.label || '')
      }
      data-test='project-select'
    />
  )
}

export default ProjectFilter
