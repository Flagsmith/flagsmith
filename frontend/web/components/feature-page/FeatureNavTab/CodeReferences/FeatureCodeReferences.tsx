import { useGetFeatureCodeReferencesQuery } from 'common/services/useCodeReferences'
import moment from 'moment'
import React from 'react'
import CodeReferencesTabHeader from './CodeReferencesTabHeader'
import CodeReferencesByRepoList, {
  CodeReferencesByRepo,
} from './CodeReferencesByRepoList'
import {
  CodeReference,
  RepositoryCodeReferenceScan,
} from 'common/types/responses'
interface FeatureCodeReferencesProps {
  featureId: number
  projectId: number
}

const FeatureCodeReferences: React.FC<FeatureCodeReferencesProps> = ({
  featureId,
  projectId,
}) => {
  const { data, isLoading } = useGetFeatureCodeReferencesQuery({
    featureId: featureId,
    projectId: projectId,
  })
  // const firstScannedAt =  null
  // data?.first_scanned_at
  //   ? moment(data.last_successful_scanned_at, 'YYYY-MM-DD')
  //   : null
  // const lastScannedAt =  null
  // data?.last_scanned_at
  //   ? moment(data.last_successful_scanned_at, 'YYYY-MM-DD')
  //   : null

  const codeReferencesByRepo = data?.reduce((acc, curr) => {
    acc[curr.repository_url] = {
      code_references: curr.code_references,
      last_feature_found_at: curr.last_feature_found_at,
      last_successful_repository_scanned_at:
        curr.last_successful_repository_scanned_at,
      repository_url: curr.repository_url,
      vcs_provider: curr.vcs_provider,
    }
    return acc
  }, {} as CodeReferencesByRepo)

  if (!data || data.length === 0) {
    return (
      <div className='flex flex-col gap-5'>
        <p className='text-sm text-gray-500'>No code references found</p>
      </div>
    )
  }

  return (
    <div className='flex flex-col gap-4'>
      {/* {firstScannedAt && lastScannedAt && (
        <CodeReferencesTabHeader
          firstScannedAt={firstScannedAt}
          lastScannedAt={lastScannedAt}
        />
      )} */}
      {codeReferencesByRepo && (
        <CodeReferencesByRepoList codeReferencesByRepo={codeReferencesByRepo} />
      )}
    </div>
  )
}

export default FeatureCodeReferences
