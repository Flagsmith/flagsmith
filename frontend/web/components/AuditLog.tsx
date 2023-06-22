import React, { FC, useEffect, useRef, useState } from 'react' // we need this to make JSX compile
import moment from 'moment'
import Utils from 'common/utils/utils'
import { AuditLogItem } from 'common/types/responses'
import { useGetAuditLogsQuery } from 'common/services/useAuditLog'
import useSearchThrottle from 'common/useSearchThrottle'
import JSONReference from './JSONReference'
import { Link } from 'react-router-dom'
import PanelSearch from './PanelSearch'

type AuditLogType = {
  environmentId: string
  projectId: string
  pageSize: number
  onSearchChange?: (search: string) => void
  onErrorChange?: (err: boolean) => void
}

const widths = [200, 200, 200]
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
    log,
  }: AuditLogItem) => {
    return (
      <Row className='list-item py-2 audit__item' key={created_date}>
        <span style={{ width: widths[0] }}>
          {moment(created_date).format('Do MMM YYYY HH:mma')}
        </span>
        <div style={{ width: widths[1] }}>
          {author?.first_name} {author?.last_name}
        </div>
        {environment?.name ? (
          <Link
            className='link-unstyled'
            style={{ width: widths[2] }}
            to={`/project/${props.projectId}/environment/${environment?.api_key}/features/`}
          >
            <Row>
              <span className='flex-row chip'>{environment?.name}</span>
            </Row>
          </Link>
        ) : (
          <div style={{ width: widths[2] }} />
        )}
        <Flex>{log}</Flex>
      </Row>
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
      icon='ion-md-browsers'
      items={projectAuditLog?.results}
      filter={envFilter}
      search={searchInput}
      onChange={(e: InputEvent) => {
        setSearchInput(Utils.safeParseEventValue(e))
      }}
      paging={{ ...(projectAuditLog || {}), page, pageSize: props.pageSize }}
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
          <span style={{ width: widths[0] }}>Date</span>
          <div style={{ width: widths[1] }}>User</div>
          <div style={{ width: widths[2] }}>Environment</div>
          <Flex>Content</Flex>
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

export default AuditLog
