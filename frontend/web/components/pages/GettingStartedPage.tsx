import React, { FC, ReactNode, useEffect } from 'react'
import PageTitle from 'components/PageTitle'
import Button from 'components/base/forms/Button'
import { IonIcon } from '@ionic/react'
import { chatbox, chevronForward, time } from 'ionicons/icons'
import loadCrisp from 'common/loadCrisp'
import Utils from 'common/utils/utils'

type ResourcesPageType = {}
import ConfigProvider from 'common/providers/ConfigProvider'
import Card from 'components/Card'
import Icon from 'components/Icon'
import { Link } from 'react-router-dom'
import { useGetProjectsQuery } from 'common/services/useProject'
import AccountStore from 'common/stores/account-store'
import classNames from 'classnames'
type GettingStartedItem = {
  duration: number
  title: string
  description: string
  link: string
  cta: string
  complete?: boolean
}
type GettingStartedItemType = {
  data: GettingStartedItem
}

const GettingStartedItem: FC<GettingStartedItemType> = ({ data }) => {
  const { complete, cta, description, duration, link, title } = data
  return (
    <div className='col-md-4 col-lg-2'>
      <div className='card bg-white h-100 shadow rounded'>
        <div
          className={classNames('p-3 d-flex h-100 flex-column', {
            'opacity-50': complete,
          })}
        >
          <div className='d-flex mb-2'>
            <span className='chip chip-secondary d-flex gap-1  align-items-center lh-1 chip chip--xs'>
              <Icon className='chip-svg-icon' width={14} name={'clock'} />
              <span>{duration} Min</span>
            </span>
          </div>
          <h5
            className={`d-flex align-items-center gap-1 ${
              complete ? 'text-success' : ''
            }`}
          >
            {title}
            {complete && <Icon fill='#27ab95' name={'checkmark-circle'} />}
          </h5>

          <h6 className='fw-normal d-flex text-muted flex-1 mb-5'>
            {description}
          </h6>
          <div className='d-flex align-items-center justify-content-between'>
            <Link to={link}>
              <Button theme='text' className='d-flex align-items-center gap-1'>
                {cta || 'Learn more'} <IonIcon icon={chevronForward} />
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

const GettingStartedPage: FC<ResourcesPageType> = ({}) => {
  async function onCrispClick() {
    loadCrisp('8857f89e-0eb5-4263-ab49-a293872b6c19')
    Utils.openChat()
  }

  const {} = useGetProjectsQuery({
    organisationId: AccountStore.getOrganisation()?.id,
  })
  const items = [
    {
      complete: true,
      description: 'Everything you need to get up-and-running with Flagsmith',
      duration: 5,
      link: '/',
      title: 'Quick Start Guide',
    },
    {
      complete: true,
      cta: 'Create Project',
      description:
        'Projects let you create and manage a set of features and configure them between multiple app environments',
      duration: 1,
      link: '/',
      title: 'Create a Project',
    },
    {
      cta: 'Create Feature',
      description:
        'The first step to using feature flags is to create one in the features page',
      duration: 1,
      link: '/',
      title: 'Create a Feature Flag',
    },
    {
      description: "Familiarise yourself with Flagsmith's features",
      duration: 1,
      link: '/',
      title: 'Feature Overview',
    },
    {
      cta: 'Explore integrations',
      description: "Familiarise yourself with Flagsmith's features",
      duration: 1,
      link: '/',
      title: 'Integrations',
    },
  ]
  return (
    <div className='bg-light100'>
      <div className='container-fluid px-3'>
        <PageTitle title={'Welcome to Flagsmith'}>
          Here's all the useful links to get you started, if you have any
          questions{' '}
          <Button
            theme='text'
            onClick={onCrispClick}
            className='text-primary gap-2'
            href=''
          >
            let us know
          </Button>
          !
        </PageTitle>
        <h6 className='mb-4'>Try things out</h6>
        <div className='row '>
          {items.map((v) => (
            <GettingStartedItem data={v} />
          ))}
        </div>
        <h6 className='my-4'>Resources</h6>
        <div className='d-flex gap-4 flex-md-row flex-column'>
          <div>
            <div className='card bg-white p-3 h-100 shadow rounded'>
              <h6 className='d-flex gap-1 mb-3 align-items-center'>
                Community Links
              </h6>
              <div className='d-flex flex-column align-items-start gap-2'>
                <Button theme='text' href='https://github.com/flagsmith'>
                  Find us on GitHub
                </Button>
                <Button theme='text' href='https://github.com/flagsmith'>
                  Contribution Guidelines
                </Button>
                <Button theme='text' href='https://github.com/flagsmith'>
                  Chat with Developers on Discord
                </Button>
                <Button theme='text' href='https://github.com/flagsmith'>
                  Listen to the Open Source podcast
                </Button>
              </div>
            </div>
          </div>
          <div className='row flex-1'>
            <div className='col-md-6 h-100'>
              <div className='card h-100 w-100 bg-white p-3 h-100 shadow rounded'></div>
            </div>
            <div className='col-md-6 h-100'>
              <div className='card bg-white p-3 h-100 shadow rounded'></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ConfigProvider(GettingStartedPage)
