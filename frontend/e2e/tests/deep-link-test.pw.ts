import { test, expect } from '../test-setup'
import { createHelpers, LONG_TIMEOUT, log } from '../helpers'
import { E2E_USER, PASSWORD } from '../config'
import Project from '../../common/project'

const PAGE_SIZE = 50
const FEATURE_COUNT = 60
const FEATURE_PREFIX = 'e2e_deeplink_'

type ApiList<T> = T[] | { results: T[] }

const unwrap = <T>(body: ApiList<T>): T[] =>
  Array.isArray(body) ? body : body.results

test.describe('Deep link to feature slideout', () => {
  test('opens the slideout for a feature on any page of the list @oss', async ({
    page,
    request,
  }) => {
    const { login } = createHelpers(page)
    const api = Project.api

    log('Authenticate against the API')
    const loginRes = await request.post(`${api}auth/login/`, {
      data: { email: E2E_USER, password: PASSWORD },
    })
    expect(loginRes.ok()).toBeTruthy()
    const { key } = await loginRes.json()
    const headers = { Authorization: `Token ${key}` }

    // Unique names per run so the flakiness check (`E2E_REPEAT` / `/e2e N`) does
    // not collide with entities created by a previous iteration.
    const runId = Date.now()

    log('Create a dedicated project and environment')
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
      data: {
        name: `Deep Link Project ${runId}`,
        organisation: organisation.id,
      },
      headers: { ...headers, 'X-E2E-Test-Auth-Token': e2eToken.trim() },
    })
    expect(projectRes.ok()).toBeTruthy()
    const project = (await projectRes.json()) as { id: number }

    const environmentRes = await request.post(`${api}environments/`, {
      data: { name: 'Development', project: project.id },
      headers,
    })
    expect(environmentRes.ok()).toBeTruthy()
    const environment = (await environmentRes.json()) as {
      id: number
      api_key: string
    }

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
})
