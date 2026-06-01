import React, { useState } from 'react'
import flagsmith from '@flagsmith/flagsmith'
import { FeatureCodeReferences } from 'common/types/responses'
import moment from 'moment'
import CodeReferenceItem from './CodeReferenceItem'
import RepoSectionHeader from './RepoSectionHeader'
import Icon from 'components/icons/Icon'
import CodeReferenceScanIndicator from './CodeReferenceScanIndicator'

interface RepoCodeReferencesSectionProps {
  repositoryScan: FeatureCodeReferences
  repositoryName: string
  featureId: number
}

const RepoCodeReferencesSection: React.FC<RepoCodeReferencesSectionProps> = ({
  featureId,
  repositoryName,
  repositoryScan,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const lastScannedAt = repositoryScan?.last_successful_repository_scanned_at
    ? moment(repositoryScan?.last_successful_repository_scanned_at)
    : null
  const lastFeatureFoundAt = repositoryScan?.last_feature_found_at
    ? moment(repositoryScan?.last_feature_found_at)
    : null

  const scanStatus =
    lastScannedAt?.isValid &&
    lastFeatureFoundAt?.isValid &&
    lastFeatureFoundAt.isSameOrAfter(lastScannedAt)
      ? 'success'
      : 'warning'

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
          onClick={() => {
            if (!isOpen) {
              flagsmith.trackEvent('code_references_expand_repo', {
                feature_id: featureId,
                refs_count: repositoryScan?.code_references?.length,
                vcs_provider: repositoryScan?.vcs_provider,
              })
            }
            setIsOpen(!isOpen)
          }}
        >
          <RepoSectionHeader
            isOpen={isOpen}
            count={repositoryScan?.code_references?.length}
            repositoryName={repositoryName}
            provider={repositoryScan?.vcs_provider}
            collapsible={true}
          />
        </Row>
        {isOpen && (
          <>
            {lastScannedAt?.isValid && (
              <Row className='flex items-center gap-1'>
                <Icon
                  name={'chevron-down'}
                  className='w-4 h-4 transparent'
                  style={{ visibility: 'hidden' }}
                />
                <p className='text-sm text-gray-500 mb-0'>
                  <strong>Last successful repository scan</strong>:{' '}
                  {lastScannedAt.format('MMM D, YYYY')}
                </p>
                <CodeReferenceScanIndicator
                  lastFeatureFoundAt={
                    lastFeatureFoundAt?.isValid ? lastFeatureFoundAt : null
                  }
                  scanStatus={scanStatus}
                />
              </Row>
            )}
            <div className='flex flex-col gap-2 mt-2'>
              {repositoryScan?.code_references?.map((codeReference) => (
                <CodeReferenceItem
                  codeReference={codeReference}
                  featureId={featureId}
                  vcsProvider={repositoryScan?.vcs_provider}
                  key={codeReference.permalink}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </>
  )
}

export default RepoCodeReferencesSection
