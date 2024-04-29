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
    <div style={{ width: '100%' }}>
      <Select
        size='select-md'
        placeholder={'Select Your Repository'}
        disabled={disabled}
        onChange={(v: any) => onChange(v?.value)}
        options={repositories?.map((i: GithubRepository) => {
          return {
            label: `${i.repository_owner} - ${i.repository_name}`,
            value: `${i.repository_owner}/${i.repository_name}`,
          }
        })}
      />
    </div>
  )
}

export default RepositoriesSelect
