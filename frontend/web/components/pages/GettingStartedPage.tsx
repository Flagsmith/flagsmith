import React, { FC, useEffect, useState } from 'react'
import PageTitle from 'components/PageTitle'
import Button from 'components/base/forms/Button'
import loadCrisp from 'common/loadCrisp'
import Utils from 'common/utils/utils'
import ConfigProvider from 'common/providers/ConfigProvider'
import Icon, { IconName } from 'components/Icon'
import { Link } from 'react-router-dom'
import { useGetProjectsQuery } from 'common/services/useProject'
import AccountStore from 'common/stores/account-store'
import classNames from 'classnames'
import { useGetProjectFlagsQuery } from 'common/services/useProjectFlag'
import { useGetSegmentsQuery } from 'common/services/useSegment'
import flagsmith from 'flagsmith'
import Tooltip from 'components/Tooltip'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import API from 'project/api'
type ResourcesPageType = {}
type GettingStartedItem = {
  duration: number
  title: string
  description: string
  link: string
  cta?: string
  icon?: IconName
  complete?: boolean
  disabledMessage?: string | null
  persistId?: string
}
type GettingStartedItemType = {
  data: GettingStartedItem
}

const resources: {
  description: string
  image: string
  title: string
  url: string
}[] = [
  {
    'description':
      'A hands-on guide covering best practices, use cases and more.',
    'image': '/static/images/welcome/featured1.png',
    'title': 'eBook | Unlock Modern Software Development with Feature Flags',
    url: 'https://www.flagsmith.com/ebook/flip-the-switch-on-modern-software-development-with-feature-flags?utm_source=app',
  },
  {
    'description': 'Set yourself up for success with these best practices.',
    'image': '/static/images/welcome/featured2.png',
    'title': 'Blog Post | Feature Flag best practices',
    url: 'https://www.flagsmith.com/blog/feature-flags-best-practices?utm_source=app',
  },
]

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
    if (data.disabledMessage) {
      return
    }
    API.trackEvent({ 'category': 'GettingStarted', 'event': data.persistId })
    if (data.persistId) {
      setLocalComplete(true)
      flagsmith.setTrait(data.persistId, Date.now())
    }
  }

  const inner = (
    <div onClick={onCTAClick} className='col-md-12 cursor-pointer'>
      <div
        className={classNames('card h-100 bg-card border-1 rounded', {
          'border-primary': complete,
        })}
      >
        <div
          className={classNames('h-100', {
            'bg-primary-opacity-5': complete,
          })}
        >
          <div
            className={classNames(
              'p-3 fs-small pt-1 d-flex h-100 flex-column mx-0',
            )}
          >
            <div className='d-flex justify-content-between align-items-center'>
              <div className='d-flex align-items-center gap-3'>
                <div
                  style={{ height: 34, width: 34 }}
                  className={
                    'd-flex rounded border-1 align-items-center justify-content-center'
                  }
                >
                  {complete ? (
                    <Icon fill='#6837fc' name={'checkmark-circle'} />
                  ) : (
                    <Icon
                      name={data.icon || 'file-text'}
                      className='text-body'
                    />
                  )}
                </div>
                <div>
                  <span
                    className={`d-flex fw-bold fs-small align-items-center mb-0 gap-1`}
                  >
                    {title}
                  </span>

                  <h6 className='fw-normal d-flex fs-small text-muted flex-1 mb-0'>
                    {description}
                  </h6>
                </div>
              </div>

              <div className='d-flex'>
                <span className='chip chip-secondary d-flex gap-1  align-items-center lh-1 chip chip--xs'>
                  <Icon className='chip-svg-icon' width={14} name={'clock'} />
                  <span>{duration} Min</span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
  if (data.disabledMessage) {
    return <Tooltip title={inner}>{data.disabledMessage}</Tooltip>
  }
  return link?.startsWith('http') ? (
    <a href={link} target={'_blank'} onClick={onCTAClick} rel='noreferrer'>
      {inner}
    </a>
  ) : (
    <Link onClick={onCTAClick} to={link}>
      {inner}
    </Link>
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
  const { data: environments } = useGetEnvironmentsQuery(
    { projectId: `${project}` },
    {
      skip: !project,
    },
  )
  const { data: segments } = useGetSegmentsQuery(
    { projectId: `${project}` },
    { skip: !project },
  )
  const environment = environments?.results?.[0]?.api_key
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
      link: `/project/${project}/environment/${environment}/features`,
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
      icon: 'pie-chart',
      link: `/project/${project}/segments`,
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
      link: 'https://docs.flagsmith.com/version-comparison',
      persistId: 'version-comparison',
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
      description:
        "Integrate Flagsmith with Flagsmith's features your existing tech stack",
      duration: 1,
      icon: 'layers',
      link: 'https://docs.flagsmith.com/integrations/',
      persistId: 'integrations',
      title: 'Integrations',
    },
  ]
  return (
    <div className='bg-light100 pb-5'>
      <div className='container-fluid mt-4 px-3'>
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
        <div className='row'>
          <div className='col-md-8'>
            <div className='card bg-card py-3 shadow rounded'>
              <h5 className='mb-3 px-3'>Getting Started</h5>
              <hr className='mt-0 py-0' />
              <div className='row px-3 row-gap-4'>
                {items.map((v, i) => (
                  <GettingStartedItem key={i} data={v} />
                ))}
              </div>
            </div>
          </div>

          <div className='col-md-4'>
            <div className='card bg-card h-100 py-3 shadow rounded'>
              <h5 className='mb-3 px-3'>Community links</h5>
              <hr className='mt-0 py-0' />
              <div className='d-flex mb-3 flex-column align-items-start gap-2'>
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
              <hr className='mt-0 py-0' />
              <h5 className='mb-3 px-3'>Resources</h5>
              <hr className='mt-0 py-0' />
              <div className='d-flex flex-column gap-4'>
                {resources.map((v, i) => (
                  <div key={i} className='col-lg-12 d-flex h-100'>
                    <div className='card bg-card p-0 h-100 border-1 rounded'>
                      <div className='d-flex align-items-center'>
                        <div>
                          <img
                            style={{
                              aspectRatio: '155 / 200',
                              height: 150,
                              objectFit: 'cover',
                              objectPosition: 'center',
                            }}
                            className=' rounded'
                            src={v.image}
                          />
                        </div>
                        <div className='me-5 h-100 d-flex flex-column justify-content-center p-3'>
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
      </div>
    </div>
  )
}

export default ConfigProvider(GettingStartedPage)
