import React, { FC } from 'react'
import TryIt from 'components/TryIt'
import EnvironmentDocumentCodeHelp from 'components/EnvironmentDocumentCodeHelp'
import Constants from 'common/constants'

type FeaturesSDKIntegrationProps = {
  projectId: number
  environmentId: string
}

export const FeaturesSDKIntegration: FC<FeaturesSDKIntegrationProps> = ({
  environmentId,
  projectId,
}) => {
  return (
    <>
      <FormGroup className='mt-5'>
        <CodeHelp
          title='1: Installing the SDK'
          snippets={Constants.codeHelp.INSTALL}
        />
        <CodeHelp
          title='2: Initialising your project'
          snippets={Constants.codeHelp.INIT(environmentId)}
        />
        <EnvironmentDocumentCodeHelp
          title='3: Providing feature defaults and support offline'
          projectId={projectId}
          environmentId={environmentId}
        />
      </FormGroup>
      <FormGroup className='pb-4'>
        <TryIt
          title='Test what values are being returned from the API on this environment'
          environmentId={environmentId}
        />
      </FormGroup>
    </>
  )
}
