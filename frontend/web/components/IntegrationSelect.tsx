import React, { FC, useMemo, useState } from 'react'
import PageTitle from './PageTitle'
import {
  integrationCategories,
  unreleasedIntegrations,
} from './pages/IntegrationsPage'
import SidebarLink from './SidebarLink'
import Input from './base/forms/Input'
import Utils from 'common/utils/utils'
import { sortBy } from 'lodash'
import ConfigProvider from 'common/providers/ConfigProvider'
import Button from './base/forms/Button'
import classNames from 'classnames'
import ModalDefault from './modals/base/ModalDefault'
import Icon from './Icon'
import { IonIcon } from '@ionic/react'
import { close } from 'ionicons/icons'

type IntegrationSelectType = {}

const IntegrationSelect: FC<IntegrationSelectType> = ({}) => {
  const [search, setSearch] = useState()
  const integrationsData = Utils.getFlagsmithValue('integration_data')
  const [category, setCategory] = useState('All')

  const allIntegrations = useMemo(() => {
    if (!integrationsData) {
      return [] as typeof unreleasedIntegrations
    }
    const value = Object.values(JSON.parse(integrationsData))
      .concat(unreleasedIntegrations)
      .filter((v) => category === 'All' || v.categories.includes(category))
    return sortBy(value, 'title') as typeof unreleasedIntegrations
  }, [integrationsData, category])
  const [selected, setSelected] = useState<string[]>([])
  const [showCustomTool, setShowCustomTool] = useState(false)
  const [customTool, setCustomTool] = useState('')

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
          <div className='col-md-4 d-none d-md-flex col-xl-2 h-100 flex-column mx-0 px-0'>
            <div className='mx-md-3'>
              {['All'].concat(integrationCategories).map((v) => (
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
          <div className='col-md-8 h-100'>
            <div className='col-md-6 mx-2 mb-2'>
              <Input
                onChange={(e: InputEvent) => {
                  const v = Utils.safeParseEventValue(e)
                  setSearch(v)
                }}
                value={search}
                type='text'
                className='w-100'
                placeholder='Search'
                search
              />
              <div className='d-flex mt-4 flex-wrap gap-2'>
                {selected.map((v) => (
                  <div className='chip--xs cursor-pointer chip'>
                    {v}
                    <IonIcon className='text-primary fs-small' name={close} />
                  </div>
                ))}
              </div>
            </div>
            <div
              style={{ height: 550 }}
              className='overflow-scroll overflow-x-hidden d-flex flex-column m-0  pt-0 custom-scroll'
            >
              <div className='row mx-0 row-cols-4  row-cols-xxl-6'>
                {allIntegrations.map((v) => {
                  const isSelected = selected.includes(v.title)
                  return (
                    <div
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
                      key={v.title}
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
              <Button style={{ width: 120 }} theme='secondary'>
                Skip
              </Button>
              <Button
                disabled={!selected?.length}
                style={{ width: 120 }}
                theme='primary'
              >
                Select Apps
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
          onChange={(e: InputEvent) => {
            setCustomTool(Utils.safeParseEventValue(e))
          }}
          value={customTool}
          placeholder='Tool name'
        />
        <div className={'text-end mt-4'}>
          <Button
            onClick={() => {
              setShowCustomTool(false)
              setSelected(selected.concat([customTool]))
            }}
          >
            Add App
          </Button>
        </div>
      </ModalDefault>
    </div>
  )
}

export default ConfigProvider(IntegrationSelect)
