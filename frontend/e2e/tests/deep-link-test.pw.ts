import { test, expect } from '../test-setup'
import { createHelpers, LONG_TIMEOUT, log } from '../helpers'
import { E2E_USER, PASSWORD, E2E_TEST_PROJECT } from '../config'
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

    // Given - an authenticated API session and a project with > PAGE_SIZE features
    log('Authenticate against the API')
    const loginRes = await request.post(`${api}auth/login/`, {
      data: { email: E2E_USER, password: PASSWORD },
    })
    expect(loginRes.ok()).toBeTruthy()
    const { key } = await loginRes.json()
    const headers = { Authorization: `Token ${key}` }

    const project = unwrap<{ id: number; name: string }>(
      await (await request.get(`${api}projects/`, { headers })).json(),
    ).find((p) => p.name === E2E_TEST_PROJECT)!
    expect(project).toBeTruthy()

    const environment = unwrap<{ id: number; name: string; api_key: string }>(
      await (
        await request.get(`${api}environments/?project=${project.id}`, {
          headers,
        })
      ).json(),
    ).find((e) => e.name === 'Development')!
    expect(environment).toBeTruthy()

    log(`Create ${FEATURE_COUNT} features`)
    // Unique names per run so the flakiness check (`E2E_REPEAT` / `/e2e N`) does
    // not collide with features created by a previous iteration.
    const runId = Date.now()
    const featureName = (i: number) =>
      `${FEATURE_PREFIX}${runId}_${String(i).padStart(3, '0')}`
    const createdFeatureIds: number[] = []

    try {
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
        createdFeatureIds.push((await res.json()).id)
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
    } finally {
      // Clean up so reruns against a persistent project don't accumulate rows.
      await Promise.all(
        createdFeatureIds.map((id) =>
          request.delete(`${api}projects/${project.id}/features/${id}/`, {
            headers,
          }),
        ),
      )
    }
  })
})
