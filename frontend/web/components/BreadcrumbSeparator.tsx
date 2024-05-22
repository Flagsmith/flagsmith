import React, { FC, ReactNode, useEffect, useRef, useState } from 'react'
import { IonIcon } from '@ionic/react'
import {
  checkmarkCircle,
  chevronDown,
  chevronUp,
  createOutline,
} from 'ionicons/icons'
import InlineModal from './InlineModal'
import Input from './base/forms/Input'
import {
  Environment,
  Organisation,
  PagedResponse,
  Project,
  User,
} from 'common/types/responses'
import AccountStore from 'common/stores/account-store'
import { useGetProjectsQuery } from 'common/services/useProject'
import AccountProvider from 'common/providers/AccountProvider'
import { RouterChildContext } from 'react-router'
import OrganisationStore from 'common/stores/organisation-store'
import AppActions from 'common/dispatcher/app-actions'
import Utils from 'common/utils/utils'
import { getStore } from 'common/store'
import { getEnvironments } from 'common/services/useEnvironment'
import classNames from 'classnames'
import Button from './base/forms/Button'
import { Link } from 'react-router-dom'
import CreateOrganisationModal from './modals/CreateOrganisation'
import { useHasPermission } from 'common/providers/Permission'
import Constants from 'common/constants'
import CreateProjectModal from './modals/CreateProject'

type BreadcrumbSeparatorType = {
  hideDropdown?: boolean
  hideSlash?: boolean
  children: ReactNode
  focus?: 'organisation' | 'project'
  projectId: string | undefined
  router: RouterChildContext['router']
}

type ItemListType = {
  items: any[] | undefined
  onHover?: (item: any) => void
  onClick: (item: any) => void
  value?: any
  hoverValue?: any
  isLoading?: boolean
  className?: string
  title: string
  footer?: ReactNode
  search?: string
}

const ItemList: FC<ItemListType> = ({
  className,
  footer,
  hoverValue,
  isLoading,
  items: _items,
  onClick,
  onHover,
  search,
  title,
  value,
}) => {
  const items = search
    ? _items?.filter((v) => {
        return v.name.toLowerCase().includes(search.toLowerCase())
      })
    : _items
  const ref = useRef(Utils.GUID())
  useEffect(() => {
    const index = items?.findIndex((v) => `${v.id}` === `${hoverValue}`)
    const el = document.getElementById(ref.current)
    const childEl = document.getElementById(`${ref.current}-${index}`)
    if (el && childEl) {
      const containerBounds = el.getBoundingClientRect()
      const elementBounds = childEl.getBoundingClientRect()
      const isInView =
        elementBounds.top >= containerBounds.top &&
        elementBounds.bottom <= containerBounds.bottom
      if (!isInView) {
        // Calculate how much to scroll the container to bring the element into view
        const scrollAmount = elementBounds.top - containerBounds.top

        // Scroll the container
        el.scrollTop += scrollAmount
      }
    }
  }, [hoverValue])
  return (
    <div
      id={ref.current}
      className={classNames('overflow-auto custom-scroll', className)}
      style={{ maxHeight: 400 }}
    >
      <div className='mb-2 text-muted'>{title}</div>
      {isLoading && (
        <div className='text-center'>
          <Loader />
        </div>
      )}
      {items?.length === 0 ? (
        search ? (
          <div className='py-2'>
            No results found for <strong>"{search}"</strong>
          </div>
        ) : (
          <div>No Results</div>
        )
      ) : null}
      {items?.map((v, i) => {
        const isActive = `${v.id}` === `${value}`
        const isHovered = `${v.id}` === `${hoverValue}`
        return (
          <a
            id={`${ref.current}-${i}`}
            onMouseEnter={() => onHover?.(v)}
            onClick={() => onClick(v)}
            key={v.id}
            className={classNames(
              'breadcrumb-link py-2 d-flex align-items-center justify-content-between',
              { active: isActive },
              { hovered: isHovered },
            )}
          >
            {v.name}
            {isActive && (
              <IonIcon className='text-primary' icon={checkmarkCircle} />
            )}
          </a>
        )
      })}
      <div className='text-center my-2'>
        <hr />
        {footer}
      </div>
    </div>
  )
}

const BreadcrumbSeparator: FC<BreadcrumbSeparatorType> = ({
  children,
  focus,
  hideDropdown,
  hideSlash,
  projectId,
  router,
}) => {
  const [open, setOpen] = useState(false)
  const [organisationSearch, setOrganisationSearch] = useState('')
  const [projectSearch, setProjectSearch] = useState('')

  const [activeOrganisation, setActiveOrganisation] = useState<string>(
    `${AccountStore.getOrganisation()?.id}`,
  )
  const [hoveredOrganisation, setHoveredOrganisation] = useState<Organisation>(
    AccountStore.getOrganisation(),
  )
  const [hoveredProject, setHoveredProject] = useState<string | undefined>(
    focus === 'organisation' ? undefined : projectId,
  )

  useEffect(() => {
    const onChangeAccountStore = () => {
      if (
        AccountStore.getOrganisation()?.id !== activeOrganisation &&
        !!AccountStore.getOrganisation()?.id
      ) {
        setActiveOrganisation(AccountStore.getOrganisation()?.id)
        setHoveredOrganisation(AccountStore.getOrganisation())
      }
    }
    AccountStore.on('change', onChangeAccountStore)
    return () => {
      OrganisationStore.off('change', onChangeAccountStore)
    }
    //eslint-disable-next-line
  }, [])

  const { data: projects } = useGetProjectsQuery(
    {
      organisationId: `${hoveredOrganisation?.id}`,
    },
    {
      skip: !hoveredOrganisation,
    },
  )

  const navigateOrganisations = (
    e: KeyboardEvent,
    organisations: Organisation[],
  ) => {
    const currentIndex = organisations
      ? organisations.findIndex((v) => `${v.id}` === `${hoveredOrganisation}`)
      : -1
    const newIndex = getNewIndex(e, currentIndex, organisations, goOrganisation)
    if (newIndex > -1) {
      setHoveredProject(undefined)
      setHoveredOrganisation(organisations![newIndex])
    }
  }

  const getNewIndex = (
    e: KeyboardEvent,
    currentIndex: number,
    items: any[] | undefined,
    go: (item: any) => void,
  ) => {
    if (!items?.length) {
      return -1
    }

    if (e.key === 'Enter' && items[currentIndex]) {
      go(items[currentIndex])
      return currentIndex
    }
    if (e.key === 'ArrowDown') {
      if (currentIndex + 1 < items?.length) {
        return currentIndex + 1
      } else {
        return items?.length - 1
      }
    } else if (e.key === 'ArrowUp') {
      return Math.max(-1, currentIndex - 1)
    }

    return -1
  }
  const navigateProjects = (e: KeyboardEvent) => {
    const currentIndex = projects
      ? projects.findIndex((v) => `${v.id}` === `${hoveredProject}`)
      : -1
    const newIndex = getNewIndex(e, currentIndex, projects, goProject)
    if (newIndex > -1) {
      setHoveredProject(`${projects![newIndex]!.id}`)
    }
  }
  const goOrganisation = (organisation: Organisation) => {
    AppActions.selectOrganisation(organisation.id)
    AppActions.getOrganisation(organisation.id)
    router.history.push(Utils.getOrganisationHomePage())
    setOpen(false)
  }
  const goProject = (project: Project) => {
    getEnvironments(getStore(), {
      projectId: `${project.id}`,
    }).then((res: { data: PagedResponse<Environment> }) => {
      router.history.push(`/project/${project.id}`)
      setOpen(false)
    })
  }
  const [hoveredSection, setHoveredSection] = useState(focus)
  const { permission: canCreateProject } = useHasPermission({
    id: hoveredOrganisation?.id,
    level: 'organisation',
    permission: Utils.getCreateProjectPermission(hoveredOrganisation),
  })
  return (
    <div className='d-flex align-items-center position-relative gap-1'>
      {children}
      {!hideDropdown && (
        <span
          onClick={() => setOpen(true)}
          className='breadcrumb-link user-select-none cursor-pointer d-flex flex-column mx-0 fs-captionSmall'
        >
          <IonIcon
            style={{ marginBottom: -2 }}
            icon={chevronUp}
            className='text-muted'
          />
          <IonIcon
            style={{ marginTop: -2 }}
            icon={chevronDown}
            className='text-muted'
          />
        </span>
      )}
      {!hideSlash && (
        <svg
          style={{ opacity: 0.5 }}
          className='with-icon_icon__MHUeb'
          data-testid='geist-icon'
          fill='none'
          height='16'
          width='16'
          shapeRendering='geometricPrecision'
          stroke='currentColor'
          strokeLinecap='round'
          strokeLinejoin='round'
          strokeWidth='1.5'
          viewBox='0 0 24 24'
        >
          <path d='M16.88 3.549L7.12 20.451'></path>
        </svg>
      )}
      <InlineModal
        hideClose
        relativeToParent
        isOpen={open}
        onClose={() => {
          setOpen(false)
          setProjectSearch('')
          setOrganisationSearch('')
        }}
        containerClassName={'p-0'}
        className={
          'inline-modal left-0 top-form-item inline-modal--sm max-w-auto'
        }
      >
        {!!open && (
          <AccountProvider>
            {({ user }: { user: User }) => {
              return (
                <div className='d-flex'>
                  <div
                    className={classNames({
                      'bg-faint rounded': hoveredSection === 'project',
                    })}
                    onMouseEnter={() => setHoveredSection('organisation')}
                    style={{ width: 260 }}
                  >
                    <Input
                      autoFocus={focus === 'organisation'}
                      onKeyDown={(e: KeyboardEvent) =>
                        navigateOrganisations(e, user.organisations)
                      }
                      onChange={(e: KeyboardEvent) => {
                        setOrganisationSearch(Utils.safeParseEventValue(e))
                      }}
                      search
                      inputClassName='border-0 bg-transparent border-bottom-1'
                      size='xSmall'
                      className='full-width'
                      placeholder='Search Organisations...'
                    />
                    <ItemList
                      search={organisationSearch}
                      className='px-2 pt-2'
                      title='Organisations'
                      hoverValue={hoveredOrganisation}
                      items={user.organisations}
                      value={activeOrganisation}
                      onHover={(organisation: Organisation) => {
                        setHoveredOrganisation(organisation)
                        setHoveredProject(undefined)
                      }}
                      onClick={goOrganisation}
                      footer={
                        Utils.canCreateOrganisation() && (
                          <Button
                            theme='outline'
                            id='create-organisation-link'
                            size='small'
                            onClick={() => {
                              setOpen(false)
                              openModal(
                                'Create Organisation',
                                <CreateOrganisationModal />,
                                'side-modal',
                              )
                            }}
                          >
                            <IonIcon
                              className='fs-small'
                              icon={createOutline}
                            />
                            Create Organisation
                          </Button>
                        )
                      }
                    />
                  </div>
                  <div
                    onMouseEnter={() => setHoveredSection('project')}
                    style={{ width: 260 }}
                    className={classNames(
                      {
                        'bg-faint rounded': hoveredSection === 'organisation',
                      },
                      'border-left-1',
                    )}
                  >
                    <Input
                      onChange={(e: InputEvent) => {
                        setProjectSearch(Utils.safeParseEventValue(e))
                      }}
                      autoFocus={focus === 'project'}
                      onKeyDown={(e: KeyboardEvent) => navigateProjects(e)}
                      search
                      className='full-width'
                      inputClassName='border-0 bg-transparent border-bottom-1'
                      size='xSmall'
                      placeholder='Search Projects...'
                    />
                    <ItemList
                      search={projectSearch}
                      className='px-2 pt-2'
                      title='Projects'
                      items={projects}
                      value={projectId}
                      hoverValue={hoveredProject}
                      onHover={(v) => setHoveredProject(v.id)}
                      onClick={goProject}
                      footer={Utils.renderWithPermission(
                        canCreateProject,
                        Constants.organisationPermissions(
                          Utils.getCreateProjectPermissionDescription(
                            AccountStore.getOrganisation(),
                          ),
                        ),
                        <Button
                          theme='outline'
                          onClick={() => {
                            document.location = `/organisation/${hoveredOrganisation.id}/projects/?create=1`
                          }}
                          id='create-organisation-link'
                          size='small'
                        >
                          <IonIcon className='fs-small' icon={createOutline} />
                          Create Project
                        </Button>,
                      )}
                    />
                  </div>
                </div>
              )
            }}
          </AccountProvider>
        )}
      </InlineModal>
    </div>
  )
}

export default BreadcrumbSeparator
