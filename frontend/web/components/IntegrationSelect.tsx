import React, { FC, useMemo, useState } from 'react'
import PageTitle from './PageTitle'
import {
  integrationCategories,
  IntegrationSummary,
} from './pages/IntegrationsPage'
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
import SidebarLink from './SidebarLink'
import Constants from 'common/constants'

type IntegrationSelectType = {
  onComplete: () => void
}

const ALL_CATEGORY = 'All'

const IntegrationSelect: FC<IntegrationSelectType> = ({ onComplete }) => {
  // Initialize search as an empty string
  const [search, setSearch] = useState<string>('')
  const integrationsData = Utils.getFlagsmithValue('integration_data')
  const [selectedCategory, setSelectedCategory] = useState<
    (typeof integrationCategories)[number]
  >(ALL_CATEGORY as any)

  // Filter integrations by category and search term
  const allIntegrations = useMemo(() => {
    if (!integrationsData) {
      return [] as typeof Constants.integrationSummaries
    }
    const parsedCategories = Object.values(JSON.parse(integrationsData)).concat(
      Constants.integrationSummaries,
    ) as IntegrationSummary[]

    const filtered = parsedCategories.filter((v) => {
      const matchesCategory =
        selectedCategory === (ALL_CATEGORY as any) ||
        v.categories.includes(selectedCategory as any)
      const matchesSearch =
        !search || v.title.toLowerCase().includes(search.toLowerCase())

      return matchesCategory && matchesSearch
    })

    return sortBy(filtered, 'title') as typeof Constants.integrationSummaries
  }, [integrationsData, selectedCategory, search])

  const [selectedIntegrations, setSelectedIntegrations] = useState<string[]>([])
  const [showCustomTool, setShowCustomTool] = useState(false)
  const [customTool, setCustomTool] = useState('')
  const [updateTools, { isLoading }] = useUpdateOnboardingMutation({})
  const skip = async () => {
    await updateTools({
      tools: {
        completed: true,
        integrations: [],
      },
    })
    onComplete()
  }
  const submit = async () => {
    await updateTools({
      tools: {
        completed: true,
        integrations: selectedIntegrations,
      },
    })
    onComplete()
  }
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
          <div className=' d-none col-md-3 d-md-flex col-xl-2 h-100 flex-column mx-0 px-0'>
            <div className='mx-md-3'>
              {[ALL_CATEGORY].concat(integrationCategories).map((v) => (
                <SidebarLink
                  key={v}
                  active={selectedCategory === v}
                  onClick={() => setSelectedCategory(v as any)}
                >
                  {v}
                </SidebarLink>
              ))}
            </div>
          </div>
          <div className='col-md-9 h-100'>
            {!!Constants.integrationCategoryDescriptions[selectedCategory] && (
              <div className='mx-4 mb-4'>
                <span className='fw-semibold'>
                  {selectedCategory} integrations
                </span>
                : {Constants.integrationCategoryDescriptions[selectedCategory]}
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
              {selectedIntegrations.map((label) => (
                <div
                  key={label}
                  onClick={() =>
                    setSelectedIntegrations(
                      selectedIntegrations.filter((target) => target !== label),
                    )
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
              style={{ height: 'calc(100vh - 400px)' }}
              className='overflow-scroll overflow-x-hidden d-flex flex-column m-0  pt-0 custom-scroll'
            >
              <div className='row mx-0 row-cols-3 row-cols-md-4  row-cols-xl-6'>
                {allIntegrations.map((v, i) => {
                  const isSelected = selectedIntegrations.includes(v.title)
                  return (
                    <div
                      data-test={`integration-${i}`}
                      key={v.title}
                      onClick={() => {
                        if (isSelected) {
                          setSelectedIntegrations(
                            selectedIntegrations.filter(
                              (selectedItem) => selectedItem !== v.title,
                            ),
                          )
                        } else {
                          setSelectedIntegrations(
                            selectedIntegrations.concat(v.title),
                          )
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
                disabled={!selectedIntegrations?.length || isLoading}
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
        onDismiss={() => {
          setCustomTool('')
          setShowCustomTool(false)
        }}
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
              setCustomTool('')
              setSelectedIntegrations(selectedIntegrations.concat([customTool]))
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
