import { FC, useState } from 'react'
import { Redirect, useRouteMatch } from 'react-router-dom'
import { skipToken } from '@reduxjs/toolkit/query'
import { useGetOrganisationAuditLogsQuery } from 'common/services/useAuditLog'
import { useGetSubscriptionMetadataQuery } from 'common/services/useSubscriptionMetadata'
import { useHasPermission } from 'common/providers/Permission'
import { OrganisationPermission } from 'common/types/permissions.types'
import Utils from 'common/utils/utils'
import PageTitle from 'components/PageTitle'
import PlanBasedBanner from 'components/PlanBasedAccess'
import Paging from 'components/Paging'
import AuditLogNoAccess from 'components/audit-log/AuditLogNoAccess'
import AuditLogList from 'components/audit-log/AuditLogList'
import OrganisationAuditLogFilters from 'components/audit-log/OrganisationAuditLogFilters'
import OrganisationAuditLogChanges from 'components/audit-log/OrganisationAuditLogChanges'
import useAuditLogFilters from 'components/audit-log/useAuditLogFilters'
import useAuditLogScopeData from 'components/audit-log/useAuditLogScopeData'
import {
  hasActiveAuditLogFilters,
  serialiseAuditLogFilters,
  toOrganisationAuditLogParams,
} from 'components/audit-log/auditLogFilters'

// The API defaults to 999 rows, which is slow.
const PAGE_SIZE = 50

const OrganisationAuditLogPage: FC = () => {
  const match = useRouteMatch<{ organisationId: string }>()
  const organisationId = Number(match.params.organisationId)
  const isEnabled = Utils.getFlagsmithHasFeature('organisation_audit_log')
  const { isSuccess: isAdminChecked, permission: isAdmin } = useHasPermission({
    id: organisationId,
    level: 'organisation',
    permission: OrganisationPermission.ADMIN,
  })
  // The API only returns this many days of logs on lower plans.
  const { data: subscriptionMeta } = useGetSubscriptionMetadataQuery(
    isEnabled && isAdmin ? { id: organisationId } : skipToken,
  )
  const auditLimitDays = subscriptionMeta?.audit_log_visibility_days
  const { clearFilters, filters, searchInput, setScope, setSearchInput } =
    useAuditLogFilters()
  const { environmentList, projectColours, projectList } = useAuditLogScopeData(
    organisationId,
    filters.scope,
    isEnabled && isAdmin,
  )

  // Back to page 1 whenever the filters change. Stored, so undoing the
  // change doesn't bring the old page back.
  const filtersKey = serialiseAuditLogFilters(filters).toString()
  const [paging, setPaging] = useState({ key: filtersKey, page: 1 })
  if (paging.key !== filtersKey) setPaging({ key: filtersKey, page: 1 })
  const page = paging.key === filtersKey ? paging.page : 1
  const goToPage = (next: number) => setPaging({ key: filtersKey, page: next })

  const { data, error, isFetching, isLoading, refetch } =
    useGetOrganisationAuditLogsQuery(
      isEnabled && isAdmin
        ? {
            organisationId,
            page,
            page_size: PAGE_SIZE,
            ...toOrganisationAuditLogParams(filters),
          }
        : skipToken,
    )

  if (!isEnabled) return <Redirect to='/404' />

  return (
    <div className='app-container container'>
      <PageTitle title='Audit log'>
        Changes across every project, plus organisation events like members,
        roles and groups.
      </PageTitle>
      {/* Only after a successful check, so a failed one never reads as no access. */}
      {isAdminChecked && !isAdmin && <AuditLogNoAccess />}
      {isAdmin && (
        <div className='d-flex flex-column gap-3'>
          {!!auditLimitDays && (
            <PlanBasedBanner
              force
              feature='AUDIT_DAYS'
              theme='description'
              title={
                <>
                  Unlock your audit log history. Currently limited to{' '}
                  <strong>{auditLimitDays} days</strong>.
                </>
              }
            />
          )}
          <OrganisationAuditLogFilters
            filters={filters}
            searchInput={searchInput}
            projects={projectList}
            environments={environmentList}
            setSearchInput={setSearchInput}
            setScope={setScope}
            onClearAll={clearFilters}
          />
          <AuditLogList
            items={data?.results}
            projectColours={projectColours}
            isLoading={isLoading || isFetching}
            error={error}
            hasFilters={hasActiveAuditLogFilters(filters)}
            onClearFilters={clearFilters}
            onRetry={refetch}
            renderDetails={(item) => (
              <OrganisationAuditLogChanges
                organisationId={organisationId}
                id={item.id}
                versionLimitDays={
                  subscriptionMeta?.feature_history_visibility_days
                }
              />
            )}
          />
          {!!data && !error && (
            <Paging
              paging={data}
              isLoading={isFetching}
              nextPage={() => goToPage(page + 1)}
              prevPage={() => goToPage(page - 1)}
              goToPage={goToPage}
            />
          )}
        </div>
      )}
    </div>
  )
}

export default OrganisationAuditLogPage
