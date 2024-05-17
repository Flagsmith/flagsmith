import React, { FC } from 'react'
import { GithubRepository } from 'common/types/responses'

export type RepositoriesSelectType = {
  disabled?: boolean
  repositories: GithubRepository[] | undefined
  onChange: (value: string) => void
}

const RepositoriesSelect: FC<RepositoriesSelectType> = ({
  disabled,
  onChange,
  repositories,
}) => {
  return (
    <div>
      <Select
        size='select-md'
        placeholder={'Select Your Repository'}
        disabled={disabled}
        onChange={(v: any) => onChange(v?.value)}
        options={repositories?.map((i: GithubRepository) => {
          return {
            label: `${i.repository_name} - ${i.repository_owner}`,
            value: `${i.repository_name}/${i.repository_owner}`,
          }
        })}
      />
    </div>
  )
}

export default RepositoriesSelect
