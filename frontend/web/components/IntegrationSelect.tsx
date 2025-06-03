import React, { FC, useMemo, useState } from 'react'
import PageTitle from './PageTitle'
import {
  integrationCategories,
  IntegrationSummary,
} from './pages/IntegrationsPage'
import SidebarLink from './SidebarLink'
import Input from './base/forms/Input'
import Utils from 'common/utils/utils'
import { sortBy } from 'lodash'
import ConfigProvider from 'common/providers/ConfigProvider'
import Button from './base/forms/Button'
import classNames from 'classnames'
import ModalDefault from './modals/base/ModalDefault'
import { IonIcon } from '@ionic/react'
import { close } from 'ionicons/icons'
import { useUpdateOnboardingMutation } from 'common/services/useOnboarding'
import InfoMessage from './InfoMessage'

type IntegrationSelectType = {
  onComplete: () => void
}

const integrationSummaries: IntegrationSummary[] = [
  {
    categories: ['Analytics'],
    image: '/static/images/integrations/hubspot.svg',
    title: 'HubSpot',
  },
  {
    categories: ['Analytics'],
    image: '/static/images/integrations/pendo.svg',
    title: 'Pendo',
  },
  {
    categories: ['Analytics'],
    image: '/static/images/integrations/adobe-analytics.png',
    title: 'Adobe Analytics',
  },
  {
    categories: ['Analytics'],
    image: '/static/images/integrations/google-analytics.svg',
    title: 'Google Analytics',
  },
  {
    categories: ['Authentication'],
    image: '/static/images/integrations/okta.svg',
    title: 'Okta',
  },
  {
    categories: ['Developer tools'],
    image: '/static/images/integrations/vs-code.svg',
    title: 'VS Code',
  },
  {
    categories: ['Infrastructure'],
    image: '/static/images/integrations/terraform.svg',
    title: 'Terraform',
  },
  {
    categories: ['Infrastructure'],
    image: '/static/images/integrations/vercel.svg',
    title: 'Vercel',
  },
  {
    categories: ['Messaging'],
    image: '/static/images/integrations/microsoft-teams.svg',
    title: 'Microsoft Teams',
  },
  {
    categories: ['Developer tools'],
    image: '/static/images/integrations/intellij.svg',
    title: 'Intellij',
  },
  {
    categories: ['Authentication'],
    image: '/static/images/integrations/ldap.png',
    title: 'LDAP',
  },
  {
    categories: ['Authentication'],
    image: '/static/images/integrations/saml.png',
    title: 'SAML',
  },
  {
    categories: ['CI/CD'],
    image: '/static/images/integrations/bitbucket.svg',
    title: 'Bitbucket',
  },
  {
    categories: ['CI/CD'],
    image: '/static/images/integrations/gitlab.svg',
    title: 'GitLab',
  },
  {
    categories: ['CI/CD'],
    image: '/static/images/integrations/azure-devops.svg',
    title: 'Azure DevOps',
  },
  {
    categories: ['CI/CD'],
    image: '/static/images/integrations/jenkins.svg',
    title: 'Jenkins',
  },
  {
    categories: ['Authentication'],
    image: '/static/images/integrations/adfs.svg',
    title: 'Microsoft Active Directory',
  },
  {
    categories: ['Monitoring'],
    image: '/static/images/integrations/appdynamics.svg',
    title: 'AppDynamics',
  },
  {
    categories: ['Monitoring'],
    image: '/static/images/integrations/aws_cloudtrail.svg',
    title: 'AWS CloudTrail',
  },
  {
    categories: ['Monitoring'],
    image: '/static/images/integrations/aws_cloudwatch.svg',
    title: 'AWS CloudWatch',
  },
  {
    categories: ['Monitoring'],
    image: '/static/images/integrations/elastic.svg',
    title: 'Elastic (ELK) Stack',
  },
  {
    categories: ['Monitoring'],
    image: '/static/images/integrations/opentelemetry.svg',
    title: 'OpenTelemetry',
  },
  {
    categories: ['Monitoring'],
    image: '/static/images/integrations/prometheus.svg',
    title: 'Prometheus',
  },
  {
    categories: ['Monitoring'],
    image: '/static/images/integrations/sumologic.svg',
    title: 'SumoLogic',
  },
]
const categoryDescriptions: Record<
  (typeof integrationCategories)[number],
  string
> = {
  'Analytics': 'Send data on what flags served to each identity.',
  'Authentication':
    'Use the Flagsmith Dashboard with your authentication provider.',
  'CI/CD': 'View your Flagsmith Flags inside your Issues and Pull Request.',
  'Developer tools': 'Interact with feature flags from your developer tools.',
  'Infrastructure':
    'Manage and evaluate your features within your infrastructure tooling.',
  'Messaging':
    'Send messages when features are created, updated and removed. Logs are tagged with the environment they came from e.g. production.',
  'Monitoring':
    'Send events when features are created, updated and removed. Logs are tagged with the environment they came from e.g. production.',
  'Webhooks':
    'Receive webhooks when your features change or when audit logs occur.',
}

const ALL_CATEGORY = 'All'

const IntegrationSelect: FC<IntegrationSelectType> = ({ onComplete }) => {
  // Initialize search as an empty string
  const [search, setSearch] = useState<string>('')
  const integrationsData = Utils.getFlagsmithValue('integration_data')
  const [category, setCategory] = useState<string>(ALL_CATEGORY)

  // Filter integrations by category and search term
  const allIntegrations = useMemo(() => {
    if (!integrationsData) {
      return [] as typeof integrationSummaries
    }
    const parsed = Object.values(JSON.parse(integrationsData)).concat(
      integrationSummaries,
    ) as IntegrationSummary[]

    const filtered = parsed.filter((v) => {
      const matchesCategory =
        category === ALL_CATEGORY || v.categories.includes(category as any)
      const matchesSearch =
        !search || v.title.toLowerCase().includes(search.toLowerCase())

      return matchesCategory && matchesSearch
    })

    return sortBy(filtered, 'title') as typeof integrationSummaries
  }, [integrationsData, category, search])

  const [selected, setSelected] = useState<string[]>([])
  const [showCustomTool, setShowCustomTool] = useState(false)
  const [customTool, setCustomTool] = useState('')
  const [updateTools, { isLoading }] = useUpdateOnboardingMutation({})
  const skip = () =>
    updateTools({
      tools: {
        completed: true,
        integrations: [],
      },
    }).then(onComplete)
  const submit = () =>
    updateTools({
      tools: {
        completed: true,
        integrations: selected,
      },
    }).then(onComplete)
  return (
    <div className='bg-light100 pb-5'>
      <div className='container-fluid mt-4 px-3'>
        <PageTitle title={'Use Feature Flags with your favourite tools'}>
          To personalise your experience and help us assist you, select the
          relevant tools you want to use feature flags with.
        </PageTitle>
      </div>
      <div className='container-fluid'>
        <div className='row'>
          <div className=' d-none col-md-4 d-md-flex col-xl-2 h-100 flex-column mx-0 px-0'>
            <div className='mx-md-3'>
              {[ALL_CATEGORY].concat(integrationCategories).map((v) => (
                <SidebarLink
                  key={v}
                  active={category === v}
                  onClick={() => setCategory(v)}
                >
                  {v}
                </SidebarLink>
              ))}
            </div>
          </div>
          <div className='col-md-9 h-100'>
            {!!categoryDescriptions[category] && (
              <div className='mx-4 mb-4'>
                <span className='fw-semibold'>{category} integrations</span>:{' '}
                {categoryDescriptions[category]}
              </div>
            )}
            <div className='col-md-6 mx-4 mb-2'>
              <Input
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                  setSearch(Utils.safeParseEventValue(e))
                }}
                value={search}
                type='text'
                className='w-100'
                placeholder='Search'
                search
              />
            </div>
            <div className='d-flex my-2 mx-4 flex-wrap gap-2'>
              {selected.map((label) => (
                <div
                  key={label}
                  onClick={() =>
                    setSelected(selected.filter((target) => target !== label))
                  }
                  className='chip--xs cursor-pointer chip'
                >
                  {label}
                  <span className='chip-icon ion'>
                    <IonIcon className='fs-small' icon={close} />
                  </span>
                </div>
              ))}
            </div>
            <div
              style={{ height: 'calc(100vh - 500px)', minHeight: 550 }}
              className='overflow-scroll overflow-x-hidden d-flex flex-column m-0  pt-0 custom-scroll'
            >
              <div className='row mx-0 row-cols-4  row-cols-xl-6'>
                {allIntegrations.map((v, i) => {
                  const isSelected = selected.includes(v.title)
                  return (
                    <div
                      data-test={`integration-${i}`}
                      key={v.title}
                      onClick={() => {
                        if (isSelected) {
                          setSelected(
                            selected.filter(
                              (selectedItem) => selectedItem !== v.title,
                            ),
                          )
                        } else {
                          setSelected(selected.concat(v.title))
                        }
                      }}
                      className='col cursor-pointer px-2 py-2 text-center'
                    >
                      <div className='bg-body rounded border-xxl-1 card p-3'>
                        <div className='mb-2'>
                          <div
                            className={classNames(
                              'rounded outline border-1 bg-white',
                              {
                                'border-primary': isSelected,
                              },
                            )}
                          >
                            <div
                              className={classNames('w-100 p-4 h-100', {
                                'bg-primary-opacity-5': isSelected,
                              })}
                            >
                              <img className='w-100' src={v.image} />
                            </div>
                          </div>
                        </div>
                        <span className='fs-small fw-semibold'>{v.title}</span>
                      </div>
                    </div>
                  )
                })}
              </div>

              <div className='my-2 text-center'>
                Not listed ?{' '}
                <Button theme='text' onClick={() => setShowCustomTool(true)}>
                  Click here
                </Button>
              </div>
            </div>
            <hr className='mb-5 mt-0' />
            <div className='sticky d-flex justify-content-end gap-4'>
              <Button
                data-test='skip-integrations'
                onClick={skip}
                style={{ width: 120 }}
                theme='secondary'
              >
                Skip
              </Button>
              <Button
                data-test='submit-integrations'
                onClick={submit}
                disabled={!selected?.length || isLoading}
                style={{ width: 120 }}
                theme='primary'
              >
                Confirm
              </Button>
            </div>
          </div>
        </div>
      </div>
      <ModalDefault
        title={'Add your favourite tool'}
        isOpen={showCustomTool}
        onDismiss={() => setShowCustomTool(false)}
        toggle={() => setShowCustomTool(!showCustomTool)}
      >
        <p>Let us know what tool you would love to use with feature flags</p>
        <Input
          className='w-100'
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
            setCustomTool(Utils.safeParseEventValue(e))
          }}
          value={customTool}
          placeholder='Enter a name...'
        />
        <div className={'text-end mt-4'}>
          <Button
            onClick={() => {
              setShowCustomTool(false)
              setSelected(selected.concat([customTool]))
            }}
          >
            Confirm
          </Button>
        </div>
      </ModalDefault>
    </div>
  )
}

export default ConfigProvider(IntegrationSelect)
