import { FC, useMemo } from 'react'
import { useGetProjectsQuery } from 'common/services/useProject'

export type ProjectFilterType = {
  organisationId: number
  value?: string
  onChange: (value: string) => void
  showAll?: boolean
  exclude?: string[]
}

const ProjectFilter: FC<ProjectFilterType> = ({
  exclude,
  onChange,
  organisationId,
  showAll,
  value,
}) => {
  const { data } = useGetProjectsQuery(
    { organisationId: `${organisationId}` },
    { skip: isNaN(organisationId) },
  )
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
      options={(showAll ? [{ label: 'All Projects', value: '' }] : [])
        .concat((data || [])?.map((v) => ({ label: v.name, value: `${v.id}` })))
        .filter((v) => !exclude?.includes(v.value))}
      onChange={(value: { value: string; label: string }) =>
        onChange(value?.value || '')
      }
    />
  )
}

export default ProjectFilter
