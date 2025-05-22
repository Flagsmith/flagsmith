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
  const [selected, setSelected] = useState([])

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
            <div className='mx-md-2'>
              {['All'].concat(integrationCategories).map((v) => (
                <SidebarLink
                  active={category === v}
                  onClick={() => setCategory(v)}
                >
                  {v}
                </SidebarLink>
              ))}
            </div>
          </div>
          <div className='col-md-8 h-100'>
            <div className='ms-3 col-md-6'>
              <Input
                onChange={(e: InputEvent) => {
                  const v = Utils.safeParseEventValue(e)
                  setSearch(v)
                }}
                value={search}
                type='text'
                className='mb-4 w-100'
                placeholder='Search'
                search
              />
            </div>
            <div
              style={{ height: 550 }}
              className='overflow-scroll d-flex flex-column m-0 p-0 custom-scroll'
            >
              <div className='d-flex flex-fill flex-wrap'>
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
                      style={{ height: 150, width: 150 }}
                      className='text-center'
                    >
                      <div className='px-3 mb-2'>
                        <div className='rounded bg-body p-2 outline border-1'>
                          <img className='w-100' src={v.image} />
                        </div>
                      </div>
                      <span className='fs-small fw-semibold'>{v.title}</span>
                    </div>
                  )
                })}
              </div>

              <div className='my-2 text-center'>
                Not listed ? <a href=''>Click here</a>
              </div>
            </div>
            <hr className='mb-5 mt-0' />
            <div className='sticky d-flex justify-content-end gap-4'>
              <Button style={{ width: 120 }} theme='secondary'>
                Skip
              </Button>
              <Button style={{ width: 120 }} theme='primary'>
                Select Apps
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ConfigProvider(IntegrationSelect)
