import type { APIRequestContext } from '@playwright/test'
import { test, expect } from '../test-setup'
import { createHelpers, LONG_TIMEOUT, log } from '../helpers'
import { E2E_USER, PASSWORD } from '../config'
import Project from '../../common/project'

const PAGE_SIZE = 50
const FEATURE_COUNT = 60
const FEATURE_PREFIX = 'e2e_deeplink_'
const COMPARE_PREFIX = 'e2e_compare_'
// One row per environment on the compare page, each serving a different value,
// so the row that opened the slideout is identifiable from its value alone.
const COMPARE_ENVIRONMENTS = ['Alpha', 'Beta', 'Gamma']

type ApiList<T> = T[] | { results: T[] }

const unwrap = <T>(body: ApiList<T>): T[] =>
  Array.isArray(body) ? body : body.results

// A project of our own per test, so a run never races another test's features
// or an earlier iteration of this one under `E2E_REPEAT`.
const createProject = async (request: APIRequestContext, name: string) => {
  const api = Project.api

  const loginRes = await request.post(`${api}auth/login/`, {
    data: { email: E2E_USER, password: PASSWORD },
  })
  expect(loginRes.ok()).toBeTruthy()
  const { key } = await loginRes.json()
  const headers = { Authorization: `Token ${key}` }

  // The seeded organisation from e2e_seed_data.py; other orgs may appear
  // concurrently (e.g. the versioning test creates one), so match by name.
  const organisation = unwrap<{ id: number; name: string }>(
    await (await request.get(`${api}organisations/`, { headers })).json(),
  ).find((o) => o.name === 'Bullet Train Ltd')!
  expect(organisation).toBeTruthy()

  // The seeded org is at its subscription's project cap; the E2E auth token
  // header marks the request as E2E so the cap check is bypassed.
  const e2eToken =
    process.env.E2E_TEST_TOKEN ??
    process.env[`E2E_TEST_TOKEN_${Project.env.toUpperCase()}`] ??
    ''
  const projectRes = await request.post(`${api}projects/`, {
    data: { name, organisation: organisation.id },
    headers: { ...headers, 'X-E2E-Test-Auth-Token': e2eToken.trim() },
  })
  expect(projectRes.ok()).toBeTruthy()
  const project = (await projectRes.json()) as { id: number }

  return { api, headers, project }
}

const createEnvironment = async (
  request: APIRequestContext,
  headers: Record<string, string>,
  api: string,
  name: string,
  projectId: number,
) => {
  const res = await request.post(`${api}environments/`, {
    data: { name, project: projectId },
    headers,
  })
  expect(res.ok()).toBeTruthy()
  return (await res.json()) as { id: number; api_key: string; name: string }
}

test.describe('Deep link to feature slideout', () => {
  test('opens the slideout for a feature on any page of the list @oss', async ({
    page,
    request,
  }) => {
    const { login } = createHelpers(page)

    // Unique names per run so the flakiness check (`E2E_REPEAT` / `/e2e N`) does
    // not collide with entities created by a previous iteration.
    const runId = Date.now()

    log('Create a dedicated project and environment')
    const { api, headers, project } = await createProject(
      request,
      `Deep Link Project ${runId}`,
    )
    const environment = await createEnvironment(
      request,
      headers,
      api,
      'Development',
      project.id,
    )

    log(`Create ${FEATURE_COUNT} features`)
    const featureName = (i: number) =>
      `${FEATURE_PREFIX}${runId}_${String(i).padStart(3, '0')}`
    const created = await Promise.all(
      Array.from({ length: FEATURE_COUNT }, (_, i) =>
        request.post(`${api}projects/${project.id}/features/`, {
          data: { name: featureName(i) },
          headers,
        }),
      ),
    )
    for (const res of created) {
      expect(res.ok()).toBeTruthy()
    }

    // The list renders sorted by name ascending, so page 1 holds the first
    // PAGE_SIZE features and a feature on page 2 never mounts a row on page 1.
    const listUrl = (pageNumber: number) =>
      `${api}projects/${project.id}/features/?environment=${environment.id}&page=${pageNumber}&page_size=${PAGE_SIZE}&sort_field=name&sort_direction=ASC`
    const page1 = await (await request.get(listUrl(1), { headers })).json()
    const page2 = await (await request.get(listUrl(2), { headers })).json()
    const onPageFeature = page1.results[0] as { id: number; name: string }
    const offPageFeature = page2.results[0] as { id: number; name: string }
    expect(onPageFeature).toBeTruthy()
    expect(offPageFeature).toBeTruthy()
    log(`On-page: ${onPageFeature.name}, off-page: ${offPageFeature.name}`)

    await login(E2E_USER, PASSWORD)
    const featuresPath = `/project/${project.id}/environment/${environment.api_key}/features`
    const slideout = page.locator('.create-feature-modal')

    // When/Then - this is the #7652 regression: a deep link to a feature that
    // is NOT on the first page previously rendered the list without opening
    // any modal, because the deep-link handler only fired for mounted rows.
    await page.goto(`${featuresPath}?feature=${offPageFeature.id}&tab=value`)
    await expect(slideout).toBeVisible({ timeout: LONG_TIMEOUT })
    await expect(slideout).toContainText(offPageFeature.name)

    // And - the existing on-page deep link still works (no regression). A
    // fresh navigation reloads the page, dismissing the previous slideout.
    await page.goto(`${featuresPath}?feature=${onPageFeature.id}&tab=value`)
    await expect(slideout).toBeVisible({ timeout: LONG_TIMEOUT })
    await expect(slideout).toContainText(onPageFeature.name)

    // And - an unknown feature id degrades gracefully (no slideout, no crash).
    await page.goto(`${featuresPath}?feature=999999999&tab=value`)
    await expect(page.locator('[data-test="features-page"]')).toBeVisible({
      timeout: LONG_TIMEOUT,
    })
    await expect(slideout).toBeHidden()
  })

  test('opens the row that was clicked, not the last one on the page @oss', async ({
    page,
    request,
  }) => {
    const { featureValueField, login } = createHelpers(page)
    const runId = Date.now()

    log('Create a project with one environment per compared value')
    const { api, headers, project } = await createProject(
      request,
      `Compare Project ${runId}`,
    )
    const environments = []
    for (const name of COMPARE_ENVIRONMENTS) {
      environments.push(
        await createEnvironment(request, headers, api, name, project.id),
      )
    }

    log('Create one feature and give it a different value in each environment')
    const featureName = `${COMPARE_PREFIX}${runId}`
    const featureRes = await request.post(
      `${api}projects/${project.id}/features/`,
      { data: { initial_value: 'unset', name: featureName }, headers },
    )
    expect(featureRes.ok()).toBeTruthy()
    const feature = (await featureRes.json()) as { id: number }

    for (const environment of environments) {
      const statesUrl = `${api}environments/${environment.api_key}/featurestates/`
      const states = await (
        await request.get(`${statesUrl}?feature=${feature.id}`, { headers })
      ).json()
      const state = states.results[0] as {
        id: number
        feature_state_value: string
      }
      // A PUT, so the whole state goes back with only the value changed. Kept
      // short: the row truncates a value at 20 characters.
      const res = await request.put(`${statesUrl}${state.id}/`, {
        data: {
          ...state,
          feature_state_value: `${environment.name.toLowerCase()}_value`,
        },
        headers,
      })
      expect(res.ok()).toBeTruthy()
    }

    await login(E2E_USER, PASSWORD)
    await page.goto(`/project/${project.id}/compare`)

    log('Select the feature to compare')
    // The page opens on Environments; the per-environment rows are behind
    // Feature Values.
    await page.getByRole('button', { name: 'Feature Values' }).click()
    // The E2E build swaps the Select for an input and one anchor per option.
    // The anchors carry no href, so they are not links in the accessibility
    // tree and their text is the only thing to select on.
    await page.getByText(featureName, { exact: true }).click()

    // The compare rows are condensed, so the value is the row's own handle.
    const rows = page.locator('[data-test^="feature-value-"]')
    await expect(rows).toHaveCount(COMPARE_ENVIRONMENTS.length, {
      timeout: LONG_TIMEOUT,
    })

    // Then - every row here is the same flag, so each one matched the id that
    // the click wrote to `?feature=` and opened the slideout in turn, leaving
    // the last environment's. Whichever environment the page orders first, the
    // slideout has to be serving the value shown on the row that was clicked.
    const firstRow = page.locator('[data-test="feature-value-0"]')
    const firstRowValue = await firstRow.locator('.feature-value').innerText()
    expect(firstRowValue).not.toEqual('')

    await firstRow.click()

    // The slideout takes its tab from the same `tab` param the compare page
    // uses for its own tabs, so it opens on one that does not exist here.
    const slideout = page.locator('#create-feature-modal')
    await expect(slideout).toBeVisible({ timeout: LONG_TIMEOUT })
    await slideout.getByRole('button', { name: 'Value', exact: true }).click()

    await expect(featureValueField()).toHaveText(firstRowValue, {
      timeout: LONG_TIMEOUT,
    })
  })
})
