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
      ...((): Pick<
        ReturnType<typeof generateMockOrganisationMetrics>[0],
        | 'api_calls_30d'
        | 'api_calls_60d'
        | 'api_calls_90d'
        | 'api_calls_allowed'
        | 'overage_30d'
        | 'overage_60d'
        | 'overage_90d'
      > => {
        // Set the allowed limit relative to actual usage so overages are realistic.
        // ~60% of orgs are within limit, ~40% slightly over (1-5%).
        const isOverLimit = Math.random() < 0.4
        const allowed = isOverLimit
          ? Math.floor(totalApiCalls * (Math.random() * 0.04 + 0.96)) // 96-100% of usage → overage is 0-4%
          : Math.floor(totalApiCalls * (Math.random() * 0.5 + 1.1)) // 110-160% of usage → within limit
        const calls60d = Math.floor(totalApiCalls * (Math.random() * 0.4 + 1.8))
        const calls90d = Math.floor(totalApiCalls * (Math.random() * 0.6 + 2.5))
        return {
          api_calls_30d: totalApiCalls,
          api_calls_60d: calls60d,
          api_calls_90d: calls90d,
          api_calls_allowed: allowed,
          overage_30d: Math.max(0, totalApiCalls - allowed),
          overage_60d: Math.max(0, calls60d - allowed * 2),
          overage_90d: Math.max(0, calls90d - allowed * 3),
        }
      })(),
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

// Realistic pipeline templates — stages have custom names, actions, and triggers.
// Multiple stages can target the same environment (e.g. progressive rollout in Production).
const pipelineTemplates = [
  {
    name: 'Progressive rollout',
    stages: [
      {
        action: 'Enable flag for segment beta_users',
        env: 'Staging',
        name: 'Beta testing',
        trigger: 'When flag is added to this stage',
      },
      {
        action: 'Enable flag for segment 10_percent_split',
        env: 'Production',
        name: 'Canary release (10%)',
        trigger: 'Wait for 3 days to proceed',
      },
      {
        action: 'Enable flag for everyone',
        env: 'Production',
        name: 'Full rollout',
        trigger: 'Wait for 7 days to proceed',
      },
    ],
  },
  {
    name: 'Standard release',
    stages: [
      {
        action: 'Enable flag for everyone',
        env: 'Development',
        name: 'Enable in dev',
        trigger: 'When flag is added to this stage',
      },
      {
        action: 'Enable flag for everyone',
        env: 'Staging',
        name: 'Enable in staging',
        trigger: 'Wait for 1 day to proceed',
      },
      {
        action: 'Enable flag for everyone',
        env: 'Production',
        name: 'Enable in production',
        trigger: 'Wait for 3 days to proceed',
      },
    ],
  },
  {
    name: 'Phased rollout (20%)',
    stages: [
      {
        action: 'Enable flag for segment 20_percent_split',
        env: 'Production',
        name: 'Activate 20% split segment',
        trigger: 'When flag is added to this stage',
      },
      {
        action: 'Enable flag for everyone',
        env: 'Production',
        name: 'Activate for all users',
        trigger: 'Wait for 14 days to proceed',
      },
    ],
  },
  {
    name: 'QA-gated release',
    stages: [
      {
        action: 'Enable flag for everyone',
        env: 'Development',
        name: 'Development',
        trigger: 'When flag is added to this stage',
      },
      {
        action: 'Enable flag for segment qa_testers',
        env: 'QA',
        name: 'QA validation',
        trigger: 'Wait for 2 days to proceed',
      },
      {
        action: 'Enable flag for everyone',
        env: 'Staging',
        name: 'Staging sign-off',
        trigger: 'Wait for 1 day to proceed',
      },
      {
        action: 'Enable flag for everyone',
        env: 'Production',
        name: 'Production release',
        trigger: 'Wait for 3 days to proceed',
      },
    ],
  },
  {
    name: 'Ring Deployment',
    stages: [
      {
        action: 'Enable flag for segment flagsmith_team',
        env: 'Production',
        name: 'Release to Internal Users',
        trigger: 'When flag is added to this stage',
      },
      {
        action: 'Enable flag for segment beta_users',
        env: 'Production',
        name: 'Release to Beta Users',
        trigger: 'Wait for 7 days to proceed to next action',
      },
      {
        action: 'Enable flag for segment uk_region',
        env: 'Production',
        name: 'Release to UK Region',
        trigger: 'Wait for 14 days to proceed to next action',
      },
      {
        action: 'Enable flag for everyone',
        env: 'Production',
        name: 'Production',
        trigger: 'Wait for 14 days to proceed to next action',
      },
    ],
  },
]

const generateMockReleasePipelineStats = (
  orgMetrics: ReturnType<typeof generateMockOrganisationMetrics>,
) => {
  const stats: Res['adminDashboardMetrics']['release_pipeline_stats'] = []
  let pipelineId = 1

  orgMetrics.forEach((org) => {
    // ~40% of projects get a pipeline (opt-in feature)
    org.projects.forEach((project) => {
      if (Math.random() > 0.4) return

      const template = pipelineTemplates[pipelineId % pipelineTemplates.length]

      const totalFeatures = Math.floor(Math.random() * 15) + 5

      // Distribute features across stages so they add up correctly:
      // features_in_stage[0] + features_in_stage[1] + ... + completedFeatures = totalFeatures
      const stageCount = template.stages.length
      let remaining = totalFeatures

      // First, decide how many completed the full pipeline (launched)
      const completedFeatures = Math.floor(
        remaining * (Math.random() * 0.4 + 0.1),
      )
      remaining -= completedFeatures

      // Distribute remaining features across stages (more in early stages)
      const inStageValues: number[] = []
      for (let s = 0; s < stageCount; s++) {
        if (s === stageCount - 1) {
          // Last stage gets whatever is left
          inStageValues.push(remaining)
        } else {
          // Earlier stages get a portion of what's left
          const portion = Math.floor(remaining * (Math.random() * 0.3 + 0.2))
          inStageValues.push(portion)
          remaining -= portion
        }
      }

      const stages = template.stages.map((tmpl, s) => ({
        action_description: tmpl.action,
        environment_name: tmpl.env,
        features_completed: 0,
        features_in_stage: inStageValues[s],
        order: s,
        stage_name: tmpl.name,
        trigger_description: tmpl.trigger,
      }))

      stats.push({
        completed_features: completedFeatures,
        is_published: Math.random() > 0.3,
        organisation_id: org.id,
        organisation_name: org.name,
        pipeline_id: pipelineId,
        pipeline_name: template.name,
        project_id: project.id,
        project_name: project.name,
        stages,
        total_features: totalFeatures,
      })

      pipelineId++
    })
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

// Integration definitions with scopes, derived from the platform config.
// Each row the API returns is org + integration + scope + count.
const integrationScopes: Record<
  string,
  ('organisation' | 'project' | 'environment')[]
> = {
  'amplitude': ['project', 'environment'],
  'datadog': ['project'],
  'dynatrace': ['project', 'environment'],
  'github': ['project'],
  'grafana': ['organisation', 'project'],
  'heap': ['project', 'environment'],
  'jira': ['organisation', 'project'],
  'mixpanel': ['project', 'environment'],
  'new-relic': ['project'],
  'rudderstack': ['project', 'environment'],
  'segment': ['project', 'environment'],
  'sentry': ['environment'],
  'slack': ['project', 'environment'],
  'webhook': ['project', 'environment'],
}

const integrationKeys = Object.keys(integrationScopes)

const generateMockIntegrationBreakdown = (
  orgMetrics: ReturnType<typeof generateMockOrganisationMetrics>,
) => {
  const data: Res['adminDashboardMetrics']['integration_breakdown'] = []

  orgMetrics.forEach((org) => {
    if (org.integration_count === 0) return

    const numTypes = Math.min(
      org.integration_count,
      Math.floor(Math.random() * 5) + 1,
    )
    const shuffled = [...integrationKeys]
      .sort(() => Math.random() - 0.5)
      .slice(0, numTypes)

    shuffled.forEach((key) => {
      const scopes = integrationScopes[key]
      scopes.forEach((scope) => {
        let count: number
        if (scope === 'organisation') {
          count = 1
        } else if (scope === 'project') {
          count = Math.floor(Math.random() * Math.min(org.project_count, 4)) + 1
        } else {
          count =
            Math.floor(Math.random() * Math.min(org.environment_count, 6)) + 1
        }
        data.push({
          count,
          integration_type: key,
          organisation_id: org.id,
          organisation_name: org.name,
          scope,
        })
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
