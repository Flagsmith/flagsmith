import React, { FC, MouseEvent } from 'react'
import { ProjectFlag, VCSProvider } from 'common/types/responses'
import Format from 'common/utils/format'
import Tooltip from 'components/Tooltip'
import VCSProviderTag from './VCSProviderTag'

type CodeReferencesTagProps = {
  counts: ProjectFlag['code_references_counts'] | undefined
  onClick?: (e: MouseEvent<HTMLDivElement>) => void
}

const CodeReferencesTag: FC<CodeReferencesTagProps> = ({ counts, onClick }) => {
  if (!counts?.length) {
    return null
  }

  const total = counts.reduce((sum, { count }) => sum + count, 0)
  const scans = Format.pluralise(total, 'time', 'times')
  const repositories = Format.pluralise(
    counts.length,
    'repository',
    'repositories',
  )
  const tag = (
    <VCSProviderTag
      count={total}
      isWarning={total === 0}
      vcsProvider={VCSProvider.GITHUB}
    />
  )

  return (
    <Tooltip
      title={
        onClick ? (
          <div onClick={onClick} className='cursor-pointer'>
            {tag}
          </div>
        ) : (
          tag
        )
      }
      place='top'
    >
      {`Scanned ${scans} in ${repositories}`}
    </Tooltip>
  )
}

export default CodeReferencesTag
