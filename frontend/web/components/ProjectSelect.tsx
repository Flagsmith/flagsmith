import React, { FC, useMemo } from 'react'
import { useGetProjectsQuery } from 'common/services/useProject'
import { Props } from 'react-select'
import { ProjectSummary } from 'common/types/responses'

type ProjectSelectType = Partial<Omit<Props, 'value' | 'onChange'>> & {
  organisationId?: number | string
  value?: string
  label?: string
  onChange: (value: string, project: ProjectSummary | null) => void
  readOnly?: boolean
  'data-test'?: string
}

const ProjectSelect: FC<ProjectSelectType> = ({
  'data-test': dataTestProp,
  label,
  onChange,
  organisationId,
  readOnly,
  value,
  ...rest
}) => {
  const { data } = useGetProjectsQuery(
    { organisationId: Number(organisationId) },
    { skip: !organisationId },
  )

  const projects = useMemo(
    () =>
      (data || [])
        .map((project) => ({
          label: project.name,
          project,
          value: `${project.id}`,
        }))
        .sort((a, b) => a.label.localeCompare(b.label)),
    [data],
  )

  const foundValue = useMemo(
    () => projects.find((project) => `${project.value}` === `${value}`),
    [value, projects],
  )

  if (readOnly) {
    return <div className='mb-2'>{foundValue?.label}</div>
  }
  return (
    <div data-test={dataTestProp}>
      <Select
        {...rest}
        className='react-select select-xsm'
        value={foundValue || { label: label || 'Select a project', value: '' }}
        options={projects}
        onChange={(v: {
          value: string
          label: string
          project: ProjectSummary
        }) => onChange(v?.value || '', v?.project || null)}
      />
    </div>
  )
}

export default ProjectSelect
