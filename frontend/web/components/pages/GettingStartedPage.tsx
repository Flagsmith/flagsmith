import React, { FC, useEffect, useState } from 'react'
import PageTitle from 'components/PageTitle'
import Button from 'components/base/forms/Button'
import { IonIcon } from '@ionic/react'
import { chevronForward } from 'ionicons/icons'
import loadCrisp from 'common/loadCrisp'
import Utils from 'common/utils/utils'
import ConfigProvider from 'common/providers/ConfigProvider'
import Icon from 'components/Icon'
import { Link } from 'react-router-dom'
import { useGetProjectsQuery } from 'common/services/useProject'
import AccountStore from 'common/stores/account-store'
import classNames from 'classnames'
import { useGetProjectFlagsQuery } from 'common/services/useProjectFlag'
import { useGetSegmentsQuery } from 'common/services/useSegment'
import flagsmith from 'flagsmith'
import Tooltip from 'components/Tooltip'

type ResourcesPageType = {}
type GettingStartedItem = {
  duration: number
  title: string
  description: string
  link: string
  cta?: string
  complete?: boolean
  disabledMessage?: string | null
  persistId?: string
}
type GettingStartedItemType = {
  data: GettingStartedItem
}

const GettingStartedItem: FC<GettingStartedItemType> = ({ data }) => {
  //Immediate complete state rather than wait for traits to come back
  const [localComplete, setLocalComplete] = useState(false)

  const { complete: _complete, cta, description, duration, link, title } = data
  const complete = data.persistId
    ? localComplete || Utils.getFlagsmithTrait(data.persistId)
    : _complete
  useEffect(() => {
    document.body.classList.add('full-screen')
    return () => {
      document.body.classList.remove('full-screen')
    }
  }, [])

  const onCTAClick = () => {
    if (data.persistId) {
      setLocalComplete(true)
      flagsmith.setTrait(data.persistId, Date.now())
    }
  }

  const button = (
    <Button
      disabled={!!data.disabledMessage}
      theme='text'
      className='d-flex align-items-center gap-1'
    >
      {cta || 'Learn more'} <IonIcon icon={chevronForward} />
    </Button>
  )

  return (
    <div className='col-md-4 col-lg-3'>
      <div
        className={classNames('card h-100 shadow rounded', {
          'bg-primary-opacity-5 opacity-75': complete,
        })}
      >
        <div className={classNames('p-3 pt-1 d-flex h-100 flex-column mx-0')}>
          <div className='d-flex justify-content-between mb-2 align-items-center'>
            <h5 className={`d-flex align-items-center mb-0 gap-1`}>
              {title}
              {complete && <Icon fill='#6837fc' name={'checkmark-circle'} />}
            </h5>

            <div className='d-flex'>
              <span className='chip chip-secondary d-flex gap-1  align-items-center lh-1 chip chip--xs'>
                <Icon className='chip-svg-icon' width={14} name={'clock'} />
                <span>{duration} Min</span>
              </span>
            </div>
          </div>

          <h6 className='fw-normal d-flex text-muted flex-1 mb-3'>
            {description}
          </h6>
          <div className='d-flex align-items-center justify-content-between'>
            {data.disabledMessage ? (
              <Tooltip title={button}>{data.disabledMessage}</Tooltip>
            ) : (
              <Link onClick={onCTAClick} to={link}>
                {button}
              </Link>
            )}
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

  const organisationId = AccountStore.getOrganisation()?.id
  const { data: projects } = useGetProjectsQuery(
    {
      organisationId,
    },
    {
      skip: !organisationId,
    },
  )
  const project = projects?.[0]?.id
  const { data: flags } = useGetProjectFlagsQuery(
    {
      project: `${project}`,
    },
    {
      skip: !project,
    },
  )
  const { data: segments } = useGetSegmentsQuery(
    { projectId: `${project}` },
    { skip: !project },
  )

  const items: GettingStartedItem[] = [
    {
      complete: !!projects?.length,
      cta: 'Create Project',
      description:
        'Projects let you create and manage a set of features and configure them between multiple app environments',
      duration: 1,
      link: `/organisation/${organisationId}/projects`,
      title: 'Create a Project',
    },
    {
      complete: !!flags?.results?.length,
      cta: 'Create Feature',
      description:
        'The first step to using feature flags is to create one in the features page',
      disabledMessage: !project
        ? 'You will need to create a project before creating your first feature'
        : null,
      duration: 1,
      link: '/',
      title: 'Create a Feature',
    },
    {
      complete: !!segments?.results?.length,
      cta: 'Create a Segment',
      description:
        'Once your features are setup you can target their rollout with segments',
      disabledMessage: !project
        ? 'You will need to create a project before creating your first segment'
        : null,
      duration: 1,
      link: '/',
      title: 'Create a Segment',
    },
    {
      complete: !!segments?.results?.length,
      cta: 'Create a Segment',
      description:
        'Once your features are setup you can target their rollout with segments',
      disabledMessage: !project
        ? 'You will need to create a project before creating your first segment'
        : null,
      duration: 1,
      link: '/',
      title: 'Version comparison',
    },
    {
      description: 'Everything you need to get up-and-running with Flagsmith',
      duration: 5,
      link: 'https://docs.flagsmith.com/quickstart/',
      persistId: 'quickstart',
      title: 'Quick Start Guide',
    },
    {
      description: "Familiarise yourself with Flagsmith's features",
      duration: 1,
      link: 'https://docs.flagsmith.com/basic-features/',
      persistId: 'basic-features',
      title: 'Feature Overview',
    },
    {
      cta: 'Explore integrations',
      description: "Familiarise yourself with Flagsmith's features",
      duration: 1,
      link: 'https://docs.flagsmith.com/integrations/',
      persistId: 'integrations',
      title: 'Integrations',
    },
  ]
  return (
    <div className='bg-light100 pb-5'>
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
        <h5 className='mb-4 mt-5'>Getting Started</h5>
        <div className='row row-gap-4'>
          {items.map((v, i) => (
            <GettingStartedItem key={i} data={v} />
          ))}
        </div>
        <h5 className='mb-4 mt-5'>Resources</h5>
        <div className='row gap-4 '>
          <div className='col-lg-2'>
            <div className='card bg-card p-3  shadow rounded'>
              <h6 className='d-flex gap-1 mb-3 align-items-center'>
                Community Links
              </h6>
              <div className='d-flex flex-column align-items-start gap-2'>
                <Button theme='text' href='https://github.com/flagsmith'>
                  <Icon name='link' />
                  Find us on GitHub
                </Button>
                <Button theme='text' href='https://github.com/flagsmith'>
                  <Icon name='link' />
                  Contribution Guidelines
                </Button>
                <Button theme='text' href='https://github.com/flagsmith'>
                  <Icon name='link' />
                  Chat with Developers on Discord
                </Button>
                <Button theme='text' href='https://github.com/flagsmith'>
                  <Icon name='link' />
                  Listen to our Podcast
                </Button>
              </div>
            </div>
          </div>
          <div className='col-lg-9 row row-gap-4'>
            {[
              {
                'description':
                  'A hands-on guide covering best practices, use cases and more.',
                'image': '/static/images/welcome/featured1.png',
                'title':
                  'eBook | Unlock Modern Software Development with Feature Flags',
                url: 'https://www.flagsmith.com/ebook/flip-the-switch-on-modern-software-development-with-feature-flags?utm_source=app',
              },
              {
                'description':
                  'Set yourself up for success with these best practices.',
                'image': '/static/images/welcome/featured2.png',
                'title': 'Blog Post | Feature Flag best practices',
                url: 'https://www.flagsmith.com/ebook/flip-the-switch-on-modern-software-development-with-feature-flags?utm_source=app',
              },
            ].map((v, i) => (
              <div key={i} className='col-lg-4 h-100'>
                <div className='card bg-card p-0 h-100 shadow rounded'>
                  <div className='row'>
                    <div className='col-md-5'>
                      <img className='img-fluid rounded' src={v.image} />
                    </div>
                    <div className='col-md-6 p-3'>
                      <a
                        href={v.url}
                        target='_blank'
                        className=''
                        rel='noreferrer'
                      >
                        <h6 className={`d-flex align-items-center gap-1`}>
                          {v.title}
                        </h6>

                        <h6 className='fw-normal d-flex text-muted flex-1'>
                          {v.description}
                        </h6>
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ConfigProvider(GettingStartedPage)
