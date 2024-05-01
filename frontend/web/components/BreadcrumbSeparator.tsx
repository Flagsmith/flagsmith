import { FC, ReactNode, useEffect, useState } from 'react'
import { IonIcon } from '@ionic/react'
import {
  checkmark,
  checkmarkCircle,
  chevronDown,
  chevronForward,
  chevronUp,
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
import { getProject, useGetProjectsQuery } from 'common/services/useProject'
import AccountProvider from 'common/providers/AccountProvider'
import { matchPath, RouterChildContext } from 'react-router'
import OrganisationStore from 'common/stores/organisation-store'
import AppActions from 'common/dispatcher/app-actions'
import Utils from 'common/utils/utils'
import { getStore } from 'common/store'
import { getEnvironments } from 'common/services/useEnvironment'
import classNames from 'classnames'

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
  onHover: (item: any) => void
  onClick: (item: any) => void
  value?: any
  isLoading?: boolean
  className?: string
  title: string
  search?: string
}

const ItemList: FC<ItemListType> = ({
  className,
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
  return (
    <div
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
      {items?.map((v) => {
        const isActive = `${v.id}` === `${value}`
        return (
          <a
            onMouseEnter={() => onHover?.(v)}
            onClick={() => onClick(v)}
            key={v.id}
            className={classNames(
              'breadcrumb-link py-2 d-flex align-items-center justify-content-between',
              { active: isActive },
            )}
          >
            {v.name}
            {isActive && (
              <IonIcon className='text-primary' icon={checkmarkCircle} />
            )}
          </a>
        )
      })}
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

  const [activeOrganisation, setActiveOrganisation] = useState<number>(
    AccountStore.getOrganisation()?.id,
  )
  const [hoveredOrganisation, setHoveredOrganisation] = useState<number>(
    AccountStore.getOrganisation()?.id,
  )

  useEffect(() => {
    const onChangeAccountStore = () => {
      if (
        AccountStore.getOrganisation()?.id !== activeOrganisation &&
        !!AccountStore.getOrganisation()?.id
      ) {
        setActiveOrganisation(AccountStore.getOrganisation()?.id)
        setHoveredOrganisation(AccountStore.getOrganisation()?.id)
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
      organisationId: `${hoveredOrganisation}`,
    },
    {
      skip: !activeOrganisation,
    },
  )

  const navigateOrganisations = (
    e: InputEvent,
    organisations: Organisation[],
  ) => {}
  const navigateProjects = (e: InputEvent) => {}
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
                  <div style={{ width: 260 }}>
                    <Input
                      autoFocus={focus === 'organisation'}
                      onKeyDown={(e: InputEvent) =>
                        navigateOrganisations(e, user.organisations)
                      }
                      onChange={(e) => {
                        setOrganisationSearch(Utils.safeParseEventValue(e))
                      }}
                      search
                      inputClassName='border-0 border-bottom-1'
                      size='xSmall'
                      className='full-width'
                      placeholder='Search Organisations...'
                    />
                    <ItemList
                      search={organisationSearch}
                      className='px-2 pt-2'
                      title='Organisations'
                      items={user.organisations}
                      value={activeOrganisation}
                      onHover={(organisation: Organisation) => {
                        setHoveredOrganisation(organisation.id)
                      }}
                      onClick={(organisation: Organisation) => {
                        AppActions.selectOrganisation(organisation.id)
                        AppActions.getOrganisation(organisation.id)
                        router.history.push(Utils.getOrganisationHomePage())
                        setOpen(false)
                      }}
                    />
                  </div>
                  <div style={{ width: 260 }} className='border-left-1'>
                    <Input
                      onChange={(e) => {
                        setProjectSearch(Utils.safeParseEventValue(e))
                      }}
                      autoFocus={focus === 'project'}
                      onKeyDown={(e: InputEvent) => navigateOrganisations(e)}
                      search
                      className='full-width'
                      inputClassName='border-0 border-bottom-1'
                      size='xSmall'
                      placeholder='Search Projects...'
                    />
                    <ItemList
                      search={projectSearch}
                      className='px-2 pt-2'
                      title='Projects'
                      items={projects}
                      value={projectId}
                      onClick={(project: Project) => {
                        getEnvironments(getStore(), {
                          projectId: `${project.id}`,
                        }).then((res: { data: PagedResponse<Environment> }) => {
                          router.history.push(`/project/${project.id}`)
                          setOpen(false)
                        })
                      }}
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
