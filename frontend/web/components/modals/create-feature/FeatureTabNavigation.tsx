import React, { FC, ReactNode } from 'react'
import { useHistory } from 'react-router-dom'
import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
import InfoMessage from 'components/InfoMessage'
import Constants from 'common/constants'
import Project from 'common/project'
import FeaturePipelineStatus from 'components/release-pipelines/FeaturePipelineStatus'
import { IonIcon } from '@ionic/react'
import { warning } from 'ionicons/icons'
import BetaFlag from 'components/BetaFlag'

type FeatureTabNavigationProps = {
  projectId: number
  projectFlagId?: number
  valueChanged: boolean
  segmentsChanged: boolean
  settingsChanged: boolean
  hasUnhealthyEvents?: boolean
  existingChangeRequest?: any
  isVersionedChangeRequest: boolean
  hideIdentityOverridesTab: boolean
  hasIntegrationWithGithub: boolean
  isVersioned: boolean
  isCodeReferencesEnabled: boolean
  viewIdentities: boolean
  valueTabContent: ReactNode
  segmentOverridesTabContent: ReactNode
  identityOverridesTabContent: ReactNode
  analyticsTabContent?: ReactNode
  featureHealthTabContent: ReactNode
  codeReferencesTabContent: ReactNode
  linksTabContent: ReactNode
  historyTabContent?: ReactNode
  settingsTabContent: ReactNode
}

const FeatureTabNavigation: FC<FeatureTabNavigationProps> = ({
  analyticsTabContent,
  codeReferencesTabContent,
  existingChangeRequest,
  featureHealthTabContent,
  hasIntegrationWithGithub,
  hasUnhealthyEvents,
  hideIdentityOverridesTab,
  historyTabContent,
  identityOverridesTabContent,
  isCodeReferencesEnabled,
  isVersioned,
  isVersionedChangeRequest,
  linksTabContent,
  projectFlagId,
  projectId,
  segmentOverridesTabContent,
  segmentsChanged,
  settingsChanged,
  settingsTabContent,
  valueChanged,
  valueTabContent,
  viewIdentities,
}) => {
  const history = useHistory()

  return (
    <>
      <FeaturePipelineStatus projectId={projectId} featureId={projectFlagId} />
      <Tabs urlParam='tab' history={history} overflowX>
        <TabItem
          data-test='value'
          tabLabelString='Value'
          tabLabel={
            <Row className='justify-content-center'>
              Value{' '}
              {valueChanged && <div className='unread ml-2 px-1'>{'*'}</div>}
            </Row>
          }
        >
          {valueTabContent}
        </TabItem>

        {(!existingChangeRequest || isVersionedChangeRequest) && (
          <TabItem
            data-test='segment_overrides'
            tabLabelString='Segment Overrides'
            tabLabel={
              <Row
                className={`justify-content-center ${
                  segmentsChanged ? 'pr-1' : ''
                }`}
              >
                Segment Overrides{' '}
                {segmentsChanged && <div className='unread ml-2 px-2'>*</div>}
              </Row>
            }
          >
            {segmentOverridesTabContent}
          </TabItem>
        )}

        {!existingChangeRequest && !hideIdentityOverridesTab && (
          <TabItem data-test='identity_overrides' tabLabel='Identity Overrides'>
            {viewIdentities ? (
              identityOverridesTabContent
            ) : (
              <InfoMessage>
                <div
                  dangerouslySetInnerHTML={{
                    __html: Constants.environmentPermissions('View Identities'),
                  }}
                />
              </InfoMessage>
            )}
          </TabItem>
        )}

        {!Project.disableAnalytics && analyticsTabContent && (
          <TabItem tabLabel={'Analytics'}>{analyticsTabContent}</TabItem>
        )}

        <TabItem
          data-test='feature_health'
          tabLabelString='Feature Health'
          tabLabel={
            <Row className='d-flex justify-content-center align-items-center pr-1 gap-1'>
              <BetaFlag flagName={'feature_health'}>
                Feature Health
                {hasUnhealthyEvents && (
                  <IonIcon
                    icon={warning}
                    style={{
                      color: Constants.featureHealth.unhealthyColor,
                      marginBottom: -2,
                    }}
                  />
                )}
              </BetaFlag>
            </Row>
          }
        >
          {featureHealthTabContent}
        </TabItem>

        {isCodeReferencesEnabled && (
          <TabItem
            tabLabel={
              <Row className='justify-content-center'>Code References</Row>
            }
          >
            {codeReferencesTabContent}
          </TabItem>
        )}

        {hasIntegrationWithGithub && projectFlagId && (
          <TabItem
            data-test='external-resources-links'
            tabLabelString='Links'
            tabLabel={<Row className='justify-content-center'>Links</Row>}
          >
            {linksTabContent}
          </TabItem>
        )}

        {!existingChangeRequest && historyTabContent && isVersioned && (
          <TabItem data-test='change-history' tabLabel='History'>
            {historyTabContent}
          </TabItem>
        )}

        {!existingChangeRequest && (
          <TabItem
            data-test='settings'
            tabLabelString='Settings'
            tabLabel={
              <Row className='justify-content-center'>
                Settings{' '}
                {settingsChanged && (
                  <div className='unread ml-2 px-1'>{'*'}</div>
                )}
              </Row>
            }
          >
            {settingsTabContent}
          </TabItem>
        )}
      </Tabs>
    </>
  )
}

export default FeatureTabNavigation
