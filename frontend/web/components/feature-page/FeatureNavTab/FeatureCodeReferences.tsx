import { useGetFeatureCodeReferencesQuery } from 'common/services/useCodeReferences'
import { useRouteContext } from 'components/providers/RouteContext'
import React from 'react'

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
  return <div>{JSON.stringify(data)}</div>
}

export default FeatureCodeReferences
