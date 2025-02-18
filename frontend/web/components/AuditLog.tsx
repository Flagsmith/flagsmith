import React, { FC, ReactNode, useEffect, useRef, useState } from 'react' // we need this to make JSX compile
import Utils from 'common/utils/utils'
import { AuditLogItem, Environment } from 'common/types/responses'
import { useGetAuditLogsQuery } from 'common/services/useAuditLog'
import useSearchThrottle from 'common/useSearchThrottle'
import { Link, withRouter } from 'react-router-dom'
import ProjectStore from 'common/stores/project-store'
import Button from './base/forms/Button'
import Tag from './tags/Tag'
import PanelSearch from './PanelSearch'
import JSONReference from './JSONReference'
import moment from 'moment'
import PlanBasedBanner from './PlanBasedAccess'
import { useGetSubscriptionMetadataQuery } from 'common/services/useSubscriptionMetadata'
import AccountStore from 'common/stores/account-store'
import { isVersionOverLimit } from 'common/services/useFeatureVersion'
import Tooltip from './Tooltip'

type AuditLogType = {
  environmentId: string
  projectId: string
  pageSize: number
  onSearchChange?: (search: string) => void
  onPageChange?: (page: number) => void
  searchPanel?: ReactNode
  onErrorChange?: (err: boolean) => void
  match: {
    params: {
      environmentId: string
      projectId: string
    }
  }
}

const widths = [210, 310, 150]
const AuditLog: FC<AuditLogType> = (props) => {
  const [page, setPage] = useState(Utils.fromParam().page ?? 1)
  const { search, searchInput, setSearchInput } = useSearchThrottle(
    Utils.fromParam().search,
    () => {
      if (searchInput !== search) {
        return setPage(1)
      }

      setPage(Utils.fromParam().page)
    },
  )
  const { data: subscriptionMeta } = useGetSubscriptionMetadataQuery({
    id: AccountStore.getOrganisation()?.id,
  })
  const [environments, setEnvironments] = useState(props.environmentId)

  useEffect(() => {
    if (environments !== props.environmentId) {
      setEnvironments(props.environmentId)
      setPage(1)
    }
  }, [props.environmentId, environments])
  useEffect(() => {
    if (props.onSearchChange) {
      props.onSearchChange(search)
    }
    //eslint-disable-next-line
  }, [search])

  useEffect(() => {
    props.onPageChange?.(page)
    //eslint-disable-next-line
  }, [page])

  const hasHadResults = useRef(false)

  const {
    data: projectAuditLog,
    isError,
    isFetching,
  } = useGetAuditLogsQuery(
    {
      environments,
      page,
      page_size: props.pageSize,
      project: props.projectId,
      search,
    },
    {
      refetchOnMountOrArgChange: true,
    },
  )

  useEffect(() => {
    props.onErrorChange?.(isError)
    //eslint-disable-next-line
  }, [])

  if (projectAuditLog?.results) {
    hasHadResults.current = true
  }

  const renderRow = ({
    author,
    created_date,
    environment,
    id,
    log,
    project,
    related_feature_id,
    related_object_type,
    related_object_uuid,
  }: AuditLogItem) => {
    const environments = ProjectStore.getEnvs() as Environment[] | null
    const index = environments?.findIndex((v) => {
      return v.id === environment?.id
    })
    const colour = index === -1 ? 0 : index
    let link: ReactNode = null
    const date = moment(created_date)
    const isVersionEvent =
      related_object_uuid && related_object_type === 'EF_VERSION' && environment
    const versionLimitDays = subscriptionMeta?.feature_history_visibility_days

    const isOverLimit = isVersionEvent
      ? isVersionOverLimit(versionLimitDays, created_date)
      : false
    const VersionButton = (
      <Button disabled={isOverLimit} theme='text'>
        View version
      </Button>
    )

    if (isVersionEvent) {
      link = (
        <Tooltip
          title={
            <div className='d-flex gap-2'>
              {isOverLimit ? (
                VersionButton
              ) : (
                <Link
                  to={`/project/${project.id}/environment/${environment.api_key}/history/${related_object_uuid}/`}
                >
                  {VersionButton}
                </Link>
              )}
              <PlanBasedBanner
                force={isOverLimit}
                feature={'VERSIONING_DAYS'}
                theme={'badge'}
              />
            </div>
          }
        >
          {isOverLimit
            ? `<div>
              Unlock your feature's entire history.<br/>Currently limited to${' '}
              <strong>${versionLimitDays} days</strong>.
            </div>`
            : ''}
        </Tooltip>
      )
    }
    const inner = (
      <Row>
        <div
          className='table-column px-3 fs-small ln-sm'
          style={{ width: widths[0] }}
        >
          {date.format('Do MMM YYYY HH:mma')}
        </div>
        <div
          className='table-column fs-small ln-sm'
          style={{ width: widths[1] }}
        >
          <div>
            {author?.first_name} {author?.last_name}
          </div>
          <div className='list-item-subtitle'>{author?.email}</div>
        </div>
        {environment?.name ? (
          <Link
            className='link-unstyled'
            style={{ width: widths[2] }}
            to={`/project/${props.projectId}/environment/${environment?.api_key}/features/`}
          >
            <Tag
              tag={{
                color: Utils.getTagColour(colour),
                label: environment?.name,
              }}
              className='chip--sm'
            />
          </Link>
        ) : (
          <div className='table-column' style={{ width: widths[2] }} />
        )}
        <Flex className='table-column fs-small ln-sm'>
          <div className='d-flex gap-2 '>
            {log}
            {link}
          </div>
        </Flex>
      </Row>
    )
    return (
      <Link
        className='fw-normal d-flex align-items-center flex-row list-item list-item-sm link-unstyled clickable'
        to={`/project/${props.projectId}/audit-log/${id}`}
      >
        {inner}
      </Link>
    )
  }

  const { env: envFilter } = Utils.fromParam()
  const auditLimitDays = subscriptionMeta?.audit_log_visibility_days

  return (
    <>
      {!!auditLimitDays && (
        <PlanBasedBanner
          className='mb-4'
          force
          feature={'AUDIT_DAYS'}
          title={
            <div>
              Unlock your audit log history. Currently limited to{' '}
              <strong>{auditLimitDays} days</strong>.
            </div>
          }
          theme={'description'}
        />
      )}
      <PanelSearch
        id='messages-list'
        title='Log entries'
        isLoading={isFetching}
        className='no-pad'
        items={projectAuditLog?.results}
        filter={envFilter}
        search={searchInput}
        searchPanel={props.searchPanel}
        onChange={(e: InputEvent) => {
          setSearchInput(Utils.safeParseEventValue(e))
        }}
        paging={{
          ...(projectAuditLog || {}),
          page,
          pageSize: props.pageSize,
        }}
        nextPage={() => {
          setPage(page + 1)
        }}
        prevPage={() => {
          setPage(page - 1)
        }}
        goToPage={(page: number) => {
          setPage(page)
        }}
        filterRow={() => true}
        renderRow={renderRow}
        header={
          <Row className='table-header'>
            <div className='table-column px-3' style={{ width: widths[0] }}>
              Date
            </div>
            <div className='table-column' style={{ width: widths[1] }}>
              User
            </div>
            <div className='table-column' style={{ width: widths[2] }}>
              Environment
            </div>
            <Flex className='table-column'>Content</Flex>
          </Row>
        }
        renderFooter={() => (
          <JSONReference
            className='mt-4 ml-2'
            title={'Audit'}
            json={projectAuditLog?.results}
          />
        )}
        renderNoResults={
          <FormGroup className='text-center'>
            You have no log messages for your project.
          </FormGroup>
        }
      />
    </>
  )
}

type AuditLogWrapperType = AuditLogType

const AuditLogWrapper: FC<AuditLogWrapperType> = (props) => {
  return (
    <PlanBasedBanner feature={'AUDIT'} theme={'page'}>
      <AuditLog {...props} />
    </PlanBasedBanner>
  )
}

export default withRouter(AuditLogWrapper as any)
