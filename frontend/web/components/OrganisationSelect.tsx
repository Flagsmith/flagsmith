import React, { FC } from 'react'
import { useGetOrganisationsQuery } from 'common/services/useOrganisation'

type OrganisationSelectProps = {
  onChange: (value: number) => void
  value?: number
}

const OrganisationSelect: FC<OrganisationSelectProps> = ({
  onChange,
  value,
}) => {
  const { data: organisations } = useGetOrganisationsQuery({})

  const selectedOrg = organisations?.results?.find((org) => org.id === value)

  return (
    <div className="d-flex">
        <Select
          className="react-select w-100"
          value={
            selectedOrg
              ? { label: selectedOrg.name, value: selectedOrg.id }
              : null
          }
          onChange={({ value }: { value: number }) => {
            onChange?.(value)
          }}
          options={organisations?.results?.map((organisation) => ({
            label: organisation.name,
            value: organisation.id,
          }))}
        />
    </div>
  )
}

export default OrganisationSelect
