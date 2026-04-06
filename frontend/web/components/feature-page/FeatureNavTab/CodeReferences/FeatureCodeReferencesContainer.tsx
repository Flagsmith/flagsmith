import React, { useEffect, useMemo, useRef } from 'react'
import flagsmith from '@flagsmith/flagsmith'
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
  const { data = [], isLoading } = useGetFeatureCodeReferencesQuery({
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

  const hasTrackedView = useRef(false)
  useEffect(() => {
    if (data.length > 0 && !hasTrackedView.current) {
      hasTrackedView.current = true
      const totalRefs = data.reduce(
        (sum, repo) => sum + repo.code_references.length,
        0,
      )
      flagsmith.trackEvent('code_references_view', {
        feature_id: featureId,
        project_id: projectId,
        repos_count: data.length,
        total_refs_count: totalRefs,
      })
    }
  }, [data, featureId, projectId])

  if (isLoading) {
    return (
      <div className='d-flex justify-content-center items-center'>
        <Loader />
      </div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div className='text-center text-muted'>
        No code references found for this feature.
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
            featureId={featureId}
          />
        ))}
    </div>
  )
}

export default FeatureCodeReferencesContainer
