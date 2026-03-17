import React, { FC } from 'react'
import { ProjectFlag, VCSProvider } from 'common/types/responses'
import VCSProviderTag from './VCSProviderTag'

type CodeReferencesTagProps = {
  projectFlag: ProjectFlag
  onClick?: (e: React.MouseEvent) => void
}

const CodeReferencesTag: FC<CodeReferencesTagProps> = ({
  onClick,
  projectFlag,
}) => {
  const hasScannedCodeReferences =
    projectFlag?.code_references_counts?.length > 0
  const codeReferencesCounts =
    projectFlag?.code_references_counts?.reduce(
      (acc, curr) => acc + curr.count,
      0,
    ) || 0

  return (
    <Tooltip
      title={
        <div
          onClick={onClick}
          style={onClick ? { cursor: 'pointer' } : undefined}
        >
          <VCSProviderTag
            count={hasScannedCodeReferences ? codeReferencesCounts : undefined}
            isWarning={hasScannedCodeReferences && codeReferencesCounts === 0}
            vcsProvider={VCSProvider.GITHUB}
          />
        </div>
      }
      place='top'
    >
      {hasScannedCodeReferences
        ? `Scanned ${codeReferencesCounts} times in ${projectFlag?.code_references_counts?.length} repositories`
        : 'See code references'}
    </Tooltip>
  )
}

export default CodeReferencesTag
