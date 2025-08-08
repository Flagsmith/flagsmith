import React, { useEffect, useState } from 'react'
import SearchableDropdown, {
  GroupLabel,
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
  const [localCurrentValue, setLocalCurrentValue] = useState(value || '')
  const { data } = useGetEnvironmentsQuery({ projectId: projectId?.toString() })
  const environments = data?.results

  useEffect(() => {
    setLocalCurrentValue(value || '')
  }, [value])

  const isEditing = localCurrentValue !== value
  const isExistingEnvironment = environments?.find(
    (environment) => environment.name === value,
  )

  const customSelectionAsOption =
    localCurrentValue && (isEditing || !isExistingEnvironment)
      ? [
          {
            label: <GroupLabel groupName='Custom selection' />,
            options: [
              {
                label: localCurrentValue?.toString(),
                value: localCurrentValue?.toString(),
              },
            ],
          },
        ]
      : []

  const environmentOptions = [
    {
      label: <GroupLabel groupName='Environments' />,
      options:
        environments?.map((environment) => ({
          label: Utils.capitalize(environment.name),
          value: environment.name,
        })) || [],
    },
  ]

  const allOptions = [...customSelectionAsOption, ...environmentOptions]

  return (
    <SearchableDropdown
      options={allOptions}
      value={value?.toString() || null}
      placeholder={'Environment'}
      noOptionsMessage={'No environment matches your search'}
      isClearable={true}
      maxMenuHeight={280}
      dataTest={dataTest}
      onInputChange={(e: string, metadata: any) => {
        if (metadata.action !== 'input-change') {
          return
        }
        setLocalCurrentValue(e)
      }}
      onBlur={() => {
        if (onChange && localCurrentValue !== value) {
          onChange(localCurrentValue?.toString() || '')
        }
      }}
      onChange={(e: OptionType) => {
        if (onChange) {
          onChange(Utils.safeParseEventValue(e?.value || ''))
        }
      }}
    />
  )
}

export default EnvironmentSelectDropdown
