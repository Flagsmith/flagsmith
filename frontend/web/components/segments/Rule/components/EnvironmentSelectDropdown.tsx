import React from 'react'
import SearchableDropdown, {
  OptionType,
} from 'components/base/SearchableDropdown'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import Utils from 'common/utils/utils'

interface EnvironmentSelectDropdownProps {
  projectId: number
  dataTest?: string
  onChange?: (value: string) => void
  value?: string | number | boolean | null
}
const EnvironmentSelectDropdown: React.FC<EnvironmentSelectDropdownProps> = ({
  dataTest,
  onChange,
  projectId,
  value,
}) => {
  const { data } = useGetEnvironmentsQuery({ projectId: projectId?.toString() })
  const environments = data?.results

  const options =
    environments?.map((environment) => ({
      label: Utils.capitalize(environment.name),
      value: environment.name,
    })) || []

  return (
    <SearchableDropdown
      options={options}
      value={
        options.find((opt) => opt.value === value?.toString())?.value ?? null
      }
      placeholder={'Environment'}
      noOptionsMessage={'No environment matches your search'}
      maxMenuHeight={240}
      dataTest={dataTest}
      onChange={(e: OptionType) => {
        if (onChange) {
          onChange(e.value)
        }
      }}
    />
  )
}

export default EnvironmentSelectDropdown
