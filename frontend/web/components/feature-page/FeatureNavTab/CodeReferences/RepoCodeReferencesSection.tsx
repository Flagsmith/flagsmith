import React, { useState } from 'react'
import { RepositoryCodeReferenceScan } from 'common/types/responses'

import CodeReferenceItem from './CodeReferenceItem'
import RepoSectionHeader from './RepoSectionHeader'

interface RepoCodeReferencesSectionProps {
  repositoryScan: RepositoryCodeReferenceScan
  repositoryName: string
}

const RepoCodeReferencesSection: React.FC<RepoCodeReferencesSectionProps> = ({
  repositoryName,
  repositoryScan,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const countByProviders = repositoryScan?.code_references?.reduce(
    (acc, curr) => {
      acc[curr.vcs_provider] = (acc[curr.vcs_provider] || 0) + 1
      return acc
    },
    {} as Record<'github' | 'gitlab' | 'bitbucket', number>,
  )

  return (
    <>
      <div
        className='flex flex-col gap-2 border-radius-sm repo-code-references-section'
        style={{
          borderRadius: '6px',
          padding: '8px 6px',
          paddingRight: '12px',
        }}
      >
        <Row
          className='flex justify-content-between items-center cursor-pointer'
          onClick={() => setIsOpen(!isOpen)}
        >
          <RepoSectionHeader
            isOpen={isOpen}
            repositoryName={repositoryName}
            countByProviders={countByProviders}
            collapsible={true}
          />
        </Row>
        {isOpen && (
          <div className='flex flex-col gap-2 mt-2'>
            <p className='text-sm text-gray-500 mb-0'>
              Last scanned at {repositoryScan?.last_successful_scanned_at}
            </p>
            {repositoryScan?.code_references?.map((codeReference) => (
              <CodeReferenceItem
                codeReference={codeReference}
                key={codeReference.permalink}
              />
            ))}
          </div>
        )}
      </div>
    </>
  )
}

export default RepoCodeReferencesSection
