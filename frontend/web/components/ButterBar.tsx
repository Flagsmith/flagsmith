import React, { useCallback, useMemo, useRef } from 'react'
import { Link } from 'react-router-dom'
import ConfigProvider from 'common/providers/ConfigProvider'
import ProjectStore from 'common/stores/project-store'
import ReactMarkdown from 'react-markdown'
import Icon from './Icon'
import Utils from 'common/utils/utils'
import { Environment, FeatureImport, Res } from 'common/types/responses'
import { useGetFeatureImportsQuery } from 'common/services/useFeatureImport'
import AppActions from 'common/dispatcher/app-actions'
import Constants from 'common/constants'

interface ButterBarProps {
  billingStatus?: string
  projectId: string
}

const ButterBar: React.FC<ButterBarProps> = ({ billingStatus, projectId }) => {
  const matches = document.location.href.match(/\/environment\/([^/]*)/)
  const environment = matches && matches[1]
  const timerRef = useRef<NodeJS.Timer>()
  const { data: featureImports, refetch } = useGetFeatureImportsQuery(
    {
      projectId,
    },
    { skip: !projectId },
  )
  const processingRef = useRef(false)
  const checkProcessing = useCallback(
    (processing: FeatureImport | undefined) => {
      if (processing) {
        if (timerRef.current) {
          clearTimeout(timerRef.current)
        }
        timerRef.current = setTimeout(() => {
          refetch().then((res) => {
            const data = res?.data as Res['featureImports']
            checkProcessing(
              data?.results?.find(
                (featureImport) => featureImport.status === 'PROCESSING',
              ),
            )
          })
        }, 2000)
      }

      if (!processing && processingRef.current && environment) {
        AppActions.refreshFeatures(projectId, environment)
      }
    },
    [environment, refetch, projectId],
  )
  const processingImport = useMemo(() => {
    const processing = featureImports?.results?.find(
      (featureImport) => featureImport.status === 'PROCESSING',
    )
    checkProcessing(processing)
    return processing
  }, [checkProcessing, featureImports])

  if (processingImport) {
    return (
      <div className='butter-bar font-weight-medium'>
        Project import in progress, this may take several minutes. <Loader />
      </div>
    )
  }
  if (environment) {
    const environmentDetail: Environment | null = ProjectStore.getEnvironment(
      environment,
    ) as Environment | null
    if (environmentDetail?.banner_text) {
      return (
        <div
          className='butter-bar font-weight-medium'
          style={{
            backgroundColor: environmentDetail.banner_colour,
            color: 'white',
          }}
        >
          {environmentDetail.banner_text}
        </div>
      )
    }
  }

  return (
    <>
      {Utils.getFlagsmithValue('butter_bar') &&
        !Utils.getFlagsmithHasFeature('read_only_mode') &&
        (!billingStatus || billingStatus === 'ACTIVE') && (
          <ReactMarkdown className='butter-bar'>
            {Utils.getFlagsmithValue('butter_bar')}
          </ReactMarkdown>
        )}
      {Utils.getFlagsmithHasFeature('read_only_mode') && (
        <div className='butter-bar'>
          Your organisation is over its usage limit, please{' '}
          <Link to={Constants.upgradeURL}>upgrade your plan</Link>.
        </div>
      )}
      {Utils.getFlagsmithHasFeature('show_dunning_banner') &&
        billingStatus === 'DUNNING' && (
          <div className='butter-bar text-white bg-danger'>
            <span className='icon-alert mr-2'>
              <Icon name='warning' fill='#fff' />
            </span>
            There was a problem with your paid subscription. Please check your
            payment method to keep your subscription active.
          </div>
        )}
    </>
  )
}

export default ConfigProvider(ButterBar)
