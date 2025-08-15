import React, { useState } from 'react'
import { CodeReference } from 'common/types/responses'

import CodeReferenceItem from './CodeReferenceItem'
import RepoSectionHeader from './RepoSectionHeader'

interface RepoCodeReferencesSectionProps {
  codeReferences: CodeReference[]
  repositoryName: string
}

const RepoCodeReferencesSection: React.FC<RepoCodeReferencesSectionProps> = ({
  codeReferences,
  repositoryName,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const countByProviders = codeReferences.reduce((acc, curr) => {
    acc[curr.vcs_provider] = (acc[curr.vcs_provider] || 0) + 1
    return acc
  }, {} as Record<'github' | 'gitlab' | 'bitbucket', number>)

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
            {codeReferences?.map((codeReference) => (
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
