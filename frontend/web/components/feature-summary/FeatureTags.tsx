import React, { FC, useMemo } from 'react'
import SegmentOverridesIcon from 'components/SegmentOverridesIcon'
import Constants from 'common/constants'
import { ProjectFlag, VCSProvider } from 'common/types/responses'
import IdentityOverridesIcon from 'components/IdentityOverridesIcon'
import TagValues from 'components/tags/TagValues'
import UnhealthyFlagWarning from './UnhealthyFlagWarning'
import StaleFlagWarning from './StaleFlagWarning'
import Tag from 'components/tags/Tag'
import Utils from 'common/utils/utils'
import { useGetHealthEventsQuery } from 'common/services/useHealthEvents'
import VCSProviderTag from 'components/tags/VCSProviderTag'

type FeatureTagsType = {
  editFeature: (tab?: string) => void
  projectFlag: ProjectFlag
}

const FeatureTags: FC<FeatureTagsType> = ({ editFeature, projectFlag }) => {
  const { data: healthEvents } = useGetHealthEventsQuery(
    { projectId: String(projectFlag.project) },
    { skip: !projectFlag?.project },
  )

  const featureUnhealthyEvents = useMemo(
    () =>
      healthEvents?.filter(
        (event) =>
          event.type === 'UNHEALTHY' && event.feature === projectFlag.id,
      ),
    [healthEvents, projectFlag],
  )
  const showPlusIndicator =
    projectFlag?.is_num_identity_overrides_complete === false

  const openFeatureHealthTab = () => {
    editFeature(Constants.featurePanelTabs.FEATURE_HEALTH)
  }
  const isFeatureHealthEnabled = Utils.getFlagsmithHasFeature('feature_health')

  const isCodeReferencesEnabled = Utils.getFlagsmithHasFeature(
    'git_code_references',
  )

  const hasScannedCodeReferences =
    isCodeReferencesEnabled && projectFlag?.code_references_counts?.length > 0
  const codeReferencesCounts = isCodeReferencesEnabled
    ? projectFlag?.code_references_counts?.reduce(
        (acc, curr) => acc + curr.count,
        0,
      )
    : 0

  return (
    <>
      <SegmentOverridesIcon
        onClick={(e) => {
          e.stopPropagation()
          editFeature(Constants.featurePanelTabs.SEGMENT_OVERRIDES)
        }}
        count={projectFlag.num_segment_overrides}
      />
      <IdentityOverridesIcon
        onClick={(e) => {
          e.stopPropagation()
          editFeature(Constants.featurePanelTabs.IDENTITY_OVERRIDES)
        }}
        count={projectFlag.num_identity_overrides}
        showPlusIndicator={showPlusIndicator}
      />
      {isCodeReferencesEnabled && hasScannedCodeReferences && (
        <Tooltip
          title={
            <VCSProviderTag
              count={codeReferencesCounts}
              isWarning={codeReferencesCounts === 0}
              vcsProvider={VCSProvider.GITHUB}
            />
          }
          place='top'
        >
          {`Scanned ${codeReferencesCounts?.toString()} times in ${projectFlag?.code_references_counts?.length?.toString()} repositories`}
        </Tooltip>
      )}
      {projectFlag.is_server_key_only && (
        <Tooltip
          title={
            <span
              className='chip me-2 chip--xs bg-primary text-white'
              style={{ border: 'none' }}
            >
              <span>{'Server-side only'}</span>
            </span>
          }
          place='top'
        >
          {'Prevent this feature from being accessed with client-side SDKs.'}
        </Tooltip>
      )}
      <TagValues
        projectId={`${projectFlag.project}`}
        value={projectFlag.tags}
        onClick={(tag) => {
          if (tag?.type === 'UNHEALTHY') {
            openFeatureHealthTab()
          }
        }}
      >
        {projectFlag.is_archived && (
          <Tag className='chip--xs' tag={Constants.archivedTag} />
        )}
      </TagValues>
      <StaleFlagWarning projectFlag={projectFlag} />
      {isFeatureHealthEnabled && (
        <UnhealthyFlagWarning
          featureUnhealthyEvents={featureUnhealthyEvents}
          onClick={(e) => {
            e?.stopPropagation()
            openFeatureHealthTab()
          }}
        />
      )}
    </>
  )
}

export default FeatureTags
