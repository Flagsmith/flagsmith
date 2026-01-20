import React, { FC } from 'react'
import { IonIcon } from '@ionic/react'
import { rocket } from 'ionicons/icons'
import Button from 'components/base/forms/Button'
import Panel from 'components/base/grid/Panel'
import { Link } from 'react-router-dom'

type FeaturesEmptyStateProps = {
  environmentId: string
  onCreateFeature: () => void
  projectId: number
  canCreateFeature: boolean
}

export const FeaturesEmptyState: FC<FeaturesEmptyStateProps> = ({
  canCreateFeature,
  environmentId,
  onCreateFeature,
  projectId,
}) => {
  return (
    <div>
      <h3>Brilliant! Now create your features.</h3>
      <FormGroup>
        <Panel
          icon='ion-ios-settings'
          title='1. configuring features per environment'
        >
          <p>
            We've created 2 Environments for you: <strong>Development</strong>{' '}
            and <strong>Production</strong>. When you create a Feature it makes
            copies of them for each Environment, allowing you to edit the values
            separately. You can create more Environments too if you need to.
          </p>
        </Panel>
      </FormGroup>
      <FormGroup>
        <Panel icon='ion-ios-rocket' title='2. creating a feature'>
          <p>
            Features in Flagsmith are made up of two different data types:
            <ul>
              <li>
                <strong>Booleans</strong>: These allows you to toggle features
                on and off:
                <p className='faint'>
                  EXAMPLE: You're working on a new messaging feature for your
                  app but only want to show it in your Development Environment.
                </p>
              </li>
              <li>
                <strong>String Values</strong>: configuration for a particular
                feature
                <p className='faint'>
                  EXAMPLE: This could be absolutely anything from a font size
                  for a website/mobile app or an environment variable for a
                  server
                </p>
              </li>
            </ul>
          </p>
        </Panel>
      </FormGroup>
      <FormGroup>
        <Panel icon='ion-ios-person' title='3. configuring features per user'>
          <p>
            When users login to your application, you can{' '}
            <strong>Identify</strong> them using one of our SDKs, this will add
            them to the Identities page. From there you can configure their
            Features. We've created an example user for you which you can see in
            the{' '}
            <Link
              className='btn-link'
              to={`/project/${projectId}/environment/${environmentId}/users`}
            >
              Identities page
            </Link>
            .
            <p className='faint'>
              EXAMPLE: You're working on a new messaging feature for your app
              but only want to show it for that Identity.
            </p>
          </p>
        </Panel>
      </FormGroup>
      <FormGroup className='text-center'>
        <Button
          disabled={!canCreateFeature}
          className='btn-lg btn-primary'
          id='show-create-feature-btn'
          data-test='show-create-feature-btn'
          onClick={onCreateFeature}
        >
          <div className='flex-row justify-content-center'>
            <IonIcon
              className='me-1'
              icon={rocket}
              style={{
                contain: 'none',
                height: '25px',
              }}
            />
            <span>Create your first Feature</span>
          </div>
        </Button>
      </FormGroup>
    </div>
  )
}
