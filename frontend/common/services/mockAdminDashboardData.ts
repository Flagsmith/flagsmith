import { Res } from 'common/types/responses'

/**
 * Mock data generator for Platform Hub MVP.
 * To be replaced with real API calls when backend is ready.
 */

const environmentNames = [
  'Development',
  'Staging',
  'Production',
  'QA',
  'UAT',
  'Canary',
]

const generateMockOrganisationMetrics = () => {
  const orgNames = [
    'Engineering Team',
    'Product Platform',
    'Mobile Apps',
    'Data Science',
    'Infrastructure',
    'Marketing Tech',
    'Customer Success',
    'Security Team',
    'Analytics Platform',
    'DevOps',
  ]

  let globalProjectId = 1
  let globalEnvId = 1

  return orgNames.map((name, i) => {
    // Generate realistic distribution (80/20 rule)
    const isHeavyUser = i < 3 // Top 3 orgs are heavy users

    const totalFlags = isHeavyUser
      ? Math.floor(Math.random() * 250) + 50
      : Math.floor(Math.random() * 70) + 10
    const activeFlags = Math.floor(totalFlags * 0.7)
    const staleFlags = totalFlags - activeFlags

    const totalUsers = isHeavyUser
      ? Math.floor(Math.random() * 80) + 20
      : Math.floor(Math.random() * 22) + 3
    const activeUsers = Math.floor(totalUsers * (Math.random() * 0.4 + 0.5))

    const projectCount = isHeavyUser
      ? Math.floor(Math.random() * 12) + 3
      : Math.floor(Math.random() * 4) + 1

    // Generate nested projects with environments
    const projects = []
    let totalApiCalls = 0
    let totalFlagEvals = 0
    let totalIdentityReqs = 0
    let totalEnvCount = 0

    for (let p = 0; p < projectCount; p++) {
      const projName = projectNames[globalProjectId % projectNames.length]
      const envCount = Math.floor(Math.random() * 3) + 2 // 2-4 environments per project
      totalEnvCount += envCount

      const environments = []
      let projApiCalls = 0
      let projFlagEvals = 0

      for (let e = 0; e < envCount; e++) {
        const envApiCalls = isHeavyUser
          ? Math.floor(Math.random() * 300000) + 20000
          : Math.floor(Math.random() * 50000) + 1000
        const envFlagEvals = Math.floor(
          envApiCalls * (Math.random() * 0.3 + 0.6),
        )

        environments.push({
          api_calls_30d: envApiCalls,
          flag_evaluations_30d: envFlagEvals,
          id: globalEnvId++,
          name: environmentNames[e % environmentNames.length],
        })

        projApiCalls += envApiCalls
        projFlagEvals += envFlagEvals
      }

      const projFlags =
        Math.floor(totalFlags / projectCount) +
        (p === 0 ? totalFlags % projectCount : 0)

      projects.push({
        api_calls_30d: projApiCalls,
        environments,
        flag_evaluations_30d: projFlagEvals,
        flags: projFlags,
        id: globalProjectId++,
        name: projName,
      })

      totalApiCalls += projApiCalls
      totalFlagEvals += projFlagEvals
    }

    totalIdentityReqs = Math.floor(totalApiCalls * 0.1)

    return {
      active_flags: activeFlags,
      active_users_30d: activeUsers,
      admin_users: isHeavyUser
        ? Math.floor(Math.random() * 6) + 2
        : Math.floor(Math.random() * 2) + 1,
      api_calls_30d: totalApiCalls,
      created_date: new Date(
        Date.now() - Math.floor(Math.random() * 730) * 24 * 60 * 60 * 1000,
      ).toISOString(),
      environment_count: totalEnvCount,
      flag_evaluations_30d: totalFlagEvals,
      id: i + 1,
      identity_requests_30d: totalIdentityReqs,
      integration_count: isHeavyUser
        ? Math.floor(Math.random() * 6) + 2
        : Math.floor(Math.random() * 3),
      name,
      project_count: projectCount,
      projects,
      stale_flags: staleFlags,
      total_flags: totalFlags,
      total_users: totalUsers,
    }
  })
}

const generateMockUsageTrends = (days = 30) => {
  const trends = []
  const baseUsage = 100000

  for (let i = 0; i < days; i++) {
    const date = new Date(Date.now() - (days - i) * 24 * 60 * 60 * 1000)

    // Add some realistic variation (weekday/weekend patterns)
    const isWeekend = date.getDay() === 0 || date.getDay() === 6
    const variation = isWeekend
      ? Math.random() * 0.2 + 0.7
      : Math.random() * 0.2 + 0.95

    trends.push({
      api_calls: Math.floor(
        baseUsage * variation * (Math.random() * 0.2 + 0.9),
      ),
      date: date.toISOString().split('T')[0],
      flag_evaluations: Math.floor(
        baseUsage * 0.8 * variation * (Math.random() * 0.2 + 0.9),
      ),
      identity_requests: Math.floor(
        baseUsage * 0.15 * variation * (Math.random() * 0.2 + 0.9),
      ),
    })
  }

  return trends
}

const getMockInstanceSummary = (
  orgMetrics: ReturnType<typeof generateMockOrganisationMetrics>,
) => {
  return {
    active_organisations: orgMetrics.filter((org) => org.active_users_30d > 0)
      .length,
    active_users: orgMetrics.reduce(
      (sum, org) => sum + org.active_users_30d,
      0,
    ),
    total_api_calls_30d: orgMetrics.reduce(
      (sum, org) => sum + org.api_calls_30d,
      0,
    ),
    total_environments: orgMetrics.reduce(
      (sum, org) => sum + org.environment_count,
      0,
    ),
    total_flags: orgMetrics.reduce((sum, org) => sum + org.total_flags, 0),
    total_integrations: orgMetrics.reduce(
      (sum, org) => sum + org.integration_count,
      0,
    ),
    total_organisations: orgMetrics.length,
    total_projects: orgMetrics.reduce((sum, org) => sum + org.project_count, 0),
    total_users: orgMetrics.reduce((sum, org) => sum + org.total_users, 0),
  }
}

const pipelineStages = ['Development', 'Staging', 'Production', 'Rollback']
const projectNames = [
  'Web App',
  'Mobile API',
  'Admin Portal',
  'Payments Service',
  'Auth Service',
  'Notifications',
  'Search Engine',
  'Data Pipeline',
]

const generateMockReleasePipelineStats = (
  orgMetrics: ReturnType<typeof generateMockOrganisationMetrics>,
) => {
  const stats: Res['adminDashboardMetrics']['release_pipeline_stats'] = []
  let projectId = 1

  orgMetrics.forEach((org) => {
    const numProjects = Math.min(org.project_count, 3)
    for (let p = 0; p < numProjects; p++) {
      const name = projectNames[(projectId - 1) % projectNames.length]
      pipelineStages.forEach((stage) => {
        stats.push({
          flag_count: Math.floor(Math.random() * 30) + 1,
          organisation_id: org.id,
          organisation_name: org.name,
          project_id: projectId,
          project_name: name,
          stage,
        })
      })
      projectId++
    }
  })

  return stats
}

const generateMockStaleFlagsPerProject = (
  orgMetrics: ReturnType<typeof generateMockOrganisationMetrics>,
) => {
  const data: Res['adminDashboardMetrics']['stale_flags_per_project'] = []
  let projectId = 1

  orgMetrics.forEach((org) => {
    const numProjects = Math.min(org.project_count, 3)
    for (let p = 0; p < numProjects; p++) {
      const name = projectNames[(projectId - 1) % projectNames.length]
      const totalFlags = Math.floor(Math.random() * 50) + 5
      const staleFlags = Math.floor(totalFlags * (Math.random() * 0.4))
      data.push({
        organisation_id: org.id,
        organisation_name: org.name,
        project_id: projectId,
        project_name: name,
        stale_flags: staleFlags,
        total_flags: totalFlags,
      })
      projectId++
    }
  })

  return data
}

const integrationTypes = [
  'Slack',
  'Datadog',
  'Segment',
  'Webhook',
  'Jira',
  'GitHub',
  'New Relic',
  'Amplitude',
]

const generateMockIntegrationBreakdown = (
  orgMetrics: ReturnType<typeof generateMockOrganisationMetrics>,
) => {
  const data: Res['adminDashboardMetrics']['integration_breakdown'] = []

  orgMetrics.forEach((org) => {
    if (org.integration_count === 0) return

    const numTypes = Math.min(
      org.integration_count,
      Math.floor(Math.random() * 4) + 1,
    )
    const shuffled = [...integrationTypes]
      .sort(() => Math.random() - 0.5)
      .slice(0, numTypes)

    shuffled.forEach((type) => {
      data.push({
        count: Math.floor(Math.random() * 3) + 1,
        integration_type: type,
        organisation_id: org.id,
        organisation_name: org.name,
      })
    })
  })

  return data
}

export const getMockAdminDashboardData = (
  days = 30,
): Res['adminDashboardMetrics'] => {
  const organisations = generateMockOrganisationMetrics()

  return {
    integration_breakdown: generateMockIntegrationBreakdown(organisations),
    organisations,
    release_pipeline_stats: generateMockReleasePipelineStats(organisations),
    stale_flags_per_project: generateMockStaleFlagsPerProject(organisations),
    summary: getMockInstanceSummary(organisations),
    usage_trends: generateMockUsageTrends(days),
  }
}
