import React, { FC } from 'react'
import { GithubRepository } from 'common/types/responses'

export type RepositoriesSelectType = {
  disabled?: boolean
  value?: string
  repositories: GithubRepository[] | undefined
  onChange: (value: string) => void
}

const RepositoriesSelect: FC<RepositoriesSelectType> = ({
  disabled,
  onChange,
  repositories,
  value,
}) => {
  const options = repositories?.map((i: GithubRepository) => {
    return {
      label: `${i.repository_name} - ${i.repository_owner}`,
      value: `${i.repository_name}/${i.repository_owner}`,
    }
  })
  return (
    <Select
      autoSelect
      className='w-100'
      size='select-md full-width'
      placeholder={'Select Your Repository'}
      disabled={disabled}
      onChange={(v: any) => onChange(v?.value)}
      options={options}
      value={options?.find((v) => v.value === value)}
    />
  )
}

export default RepositoriesSelect
