import { FC } from 'react'
import { ProjectFlag } from 'common/types/responses'
import { useGetFeatureListQuery } from 'common/services/useProjectFlag'
import { useProjectEnvironments } from 'common/hooks/useProjectEnvironments'
import useDebouncedSearch from 'common/useDebouncedSearch'

export type FeatureSelectOption = {
  feature: ProjectFlag
  label: string
  value: number
}

type FeatureSelectProps = {
  'data-test'?: string
  className?: string
  disabled?: boolean
  // Feature ids to leave out, e.g. the feature being edited and the ones
  // already chosen.
  ignore?: number[]
  environmentId: string
  onChange: (feature: ProjectFlag) => void
  placeholder?: string
  projectId: number
  value?: number | null
}

const FeatureSelect: FC<FeatureSelectProps> = ({
  className,
  disabled,
  environmentId,
  ignore,
  onChange,
  placeholder,
  projectId,
  value,
  ...rest
}) => {
  const { search, searchInput, setSearchInput } = useDebouncedSearch()
  // getFeatureList parses environmentId as the numeric id, not the api key.
  const { getEnvironmentIdFromKey } = useProjectEnvironments(projectId)
  const numericEnvId = getEnvironmentIdFromKey(environmentId)

  const { data, isLoading } = useGetFeatureListQuery(
    {
      environmentId: String(numericEnvId ?? ''),
      page: 1,
      // One page has to cover the project, or a feature past the first page is
      // unpickable unless the user happens to search for it.
      page_size: 999,
      projectId,
      search: search || undefined,
    },
    { skip: !numericEnvId },
  )

  const options = (data?.results ?? [])
    .filter((feature) => !ignore?.includes(feature.id))
    .map((feature) => ({
      feature,
      label: feature.name,
      value: feature.id,
    }))

  return (
    //@ts-ignore Select is a global defined in web/project/project-components.js
    <Select
      data-test={rest['data-test']}
      className={className}
      isClearable={false}
      isDisabled={disabled}
      isLoading={isLoading}
      inputValue={searchInput}
      // The menu is portalled because callers put this inside containers that
      // clip it, e.g. the dependencies panel's rounded overflow.
      menuPortalTarget={document.body}
      menuPosition='absolute'
      menuPlacement='auto'
      onInputChange={setSearchInput}
      onChange={(option: FeatureSelectOption | null) => {
        if (option) onChange(option.feature)
      }}
      options={options}
      placeholder={placeholder}
      value={options.find((option) => option.value === value) ?? null}
    />
  )
}

export default FeatureSelect
