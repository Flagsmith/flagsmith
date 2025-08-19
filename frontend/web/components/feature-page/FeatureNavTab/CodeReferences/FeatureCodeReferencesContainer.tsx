import React, { useMemo } from 'react'
import { useGetFeatureCodeReferencesQuery } from 'common/services/useCodeReferences'
import RepoCodeReferencesSection from './components/RepoCodeReferencesSection'
import { FeatureCodeReferences } from 'common/types/responses'

interface FeatureCodeReferencesContainerProps {
  featureId: number
  projectId: number
}

type CodeReferencesByRepo = Record<string, FeatureCodeReferences>

const FeatureCodeReferencesContainer: React.FC<
  FeatureCodeReferencesContainerProps
> = ({ featureId, projectId }) => {
  const { data, isLoading } = useGetFeatureCodeReferencesQuery({
    featureId: featureId,
    projectId: projectId,
  })

  const codeReferencesByRepo = useMemo(
    () =>
      data?.reduce((acc, curr) => {
        acc[curr.repository_url] = {
          code_references: curr.code_references,
          last_feature_found_at: curr.last_feature_found_at,
          last_successful_repository_scanned_at:
            curr.last_successful_repository_scanned_at,
          repository_url: curr.repository_url,
          vcs_provider: curr.vcs_provider,
        }
        return acc
      }, {} as CodeReferencesByRepo),
    [data],
  )

  if (!data || data.length === 0) {
    return (
      <div className='flex flex-col gap-5'>
        <p className='text-sm text-gray-500'>No code references found</p>
      </div>
    )
  }
  const scannedRepos = Object.keys(codeReferencesByRepo || {})
  return (
    <div className='flex flex-col gap-4'>
      {scannedRepos?.length > 0 &&
        codeReferencesByRepo &&
        scannedRepos.map((repo) => (
          <RepoCodeReferencesSection
            key={codeReferencesByRepo[repo].repository_url}
            repositoryName={codeReferencesByRepo[repo].repository_url}
            repositoryScan={codeReferencesByRepo[repo]}
          />
        ))}
    </div>
  )
}

export default FeatureCodeReferencesContainer
