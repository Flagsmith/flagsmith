import React, { FC, ReactNode, useEffect, useRef, useState } from 'react' // we need this to make JSX compile
import moment from 'moment'
import Utils from 'common/utils/utils'
import { AuditLogItem, Environment } from 'common/types/responses'
import { useGetAuditLogsQuery } from 'common/services/useAuditLog'
import useSearchThrottle from 'common/useSearchThrottle'
import JSONReference from './JSONReference'
import { Link, withRouter } from 'react-router-dom'
import PanelSearch from './PanelSearch'
import ProjectStore from 'common/stores/project-store'
import Tag from './tags/Tag'

type AuditLogType = {
  environmentId: string
  projectId: string
  pageSize: number
  onSearchChange?: (search: string) => void
  searchPanel?: ReactNode
  onErrorChange?: (err: boolean) => void
  match: {
    params: {
      environmentId: string
      projectId: string
    }
  }
}

const widths = [210, 210, 210]
const AuditLog: FC<AuditLogType> = (props) => {
  const [page, setPage] = useState(1)
  const { search, searchInput, setSearchInput } = useSearchThrottle(
    Utils.fromParam().search,
    () => {
      setPage(1)
    },
  )
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

  const hasHadResults = useRef(false)

  const {
    data: projectAuditLog,
    isError,
    isFetching,
  } = useGetAuditLogsQuery({
    environments,
    page,
    page_size: props.pageSize,
    project: props.projectId,
    search,
  })

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
  }: AuditLogItem) => {
    const environments = ProjectStore.getEnvs() as Environment[] | null
    const index = environments?.findIndex((v) => {
      return v.id === environment?.id
    })
    const colour = index === -1 ? 0 : index
    const inner = (
      <Row>
        <div
          className='table-column px-3 fs-small ln-sm'
          style={{ width: widths[0] }}
        >
          {moment(created_date).format('Do MMM YYYY HH:mma')}
        </div>
        <div
          className='table-column fs-small ln-sm'
          style={{ width: widths[1] }}
        >
          {author?.first_name} {author?.last_name}
        </div>
        {environment?.name ? (
          <Link
            className='link-unstyled'
            style={{ width: widths[2] }}
            to={`/project/${props.projectId}/environment/${environment?.api_key}/features/`}
          >
            <Row>
              <Tag
                tag={{
                  color: Utils.getTagColour(colour),
                  label: environment?.name,
                }}
                className='chip--sm'
              />
            </Row>
          </Link>
        ) : (
          <div className='table-column' style={{ width: widths[2] }} />
        )}
        <Flex className='table-column fs-small ln-sm'>{log}</Flex>
      </Row>
    )
    return (
      <Link
        className='fw-normal d-flex align-items-center flex-row list-item list-item-sm link-unstyled clickable'
        to={`/project/${props.projectId}/environment/${props.match.params.environmentId}/audit-log/${id}`}
      >
        {inner}
      </Link>
    )
  }

  const { env: envFilter } = Utils.fromParam()

  const hasRbacPermission = Utils.getPlansPermission('AUDIT')
  if (!hasRbacPermission) {
    return (
      <div>
        <div className='text-center'>
          To access this feature please upgrade your account to scaleup or
          higher.
        </div>
      </div>
    )
  }

  return (
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
  )
}

export default withRouter(AuditLog)
