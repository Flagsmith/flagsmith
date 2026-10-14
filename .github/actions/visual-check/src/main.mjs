// @ts-check
import fs from 'node:fs'
import { renderOutput } from './markdown.mjs'
import { readReport } from './report.mjs'
import {
  commitFiles,
  createCheckRun,
  listOpenPullRequests,
  pruneBranch,
  rawUrl,
} from './github.mjs'

/**
 * @typedef {import('./report.mjs').Comparison} Comparison
 * @typedef {import('./markdown.mjs').ImageUrls} ImageUrls
 */

const env = process.env
/** @param {string} name */
const input = (name) => (env[`INPUT_${name}`] || '').trim()

const context = {
  apiUrl: env.GITHUB_API_URL || 'https://api.github.com',
  repository: /** @type {string} */ (env.GITHUB_REPOSITORY),
  serverUrl: env.GITHUB_SERVER_URL || 'https://github.com',
  token: input('GITHUB_TOKEN'),
}
const branch = input('IMAGES_BRANCH')

/** @param {string} message */
const warn = (message) => console.log(`::warning title=visual-check::${message}`)

/** @param {Record<string, string | number>} values */
const setOutputs = (values) => {
  if (!env.GITHUB_OUTPUT) return
  const lines = Object.entries(values).map(([key, value]) => `${key}=${value}`)
  fs.appendFileSync(env.GITHUB_OUTPUT, `${lines.join('\n')}\n`)
}

/** @param {string} markdown */
const writeSummary = (markdown) => {
  if (env.GITHUB_STEP_SUMMARY) fs.appendFileSync(env.GITHUB_STEP_SUMMARY, `${markdown}\n`)
}

const pullRequestNumber = () => {
  if (!env.GITHUB_EVENT_PATH) return undefined
  const event = JSON.parse(fs.readFileSync(env.GITHUB_EVENT_PATH, 'utf8'))
  return /** @type {number | undefined} */ (event.pull_request?.number)
}

/** @param {string} value */
const slug = (value) =>
  value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')

/**
 * @param {Comparison[]} comparisons
 * @returns {Promise<Map<Comparison, ImageUrls>>}
 */
const uploadImages = async (comparisons) => {
  /** @type {Map<Comparison, ImageUrls>} */
  const urls = new Map()
  if (!comparisons.length) return urls

  const pr = pullRequestNumber()
  const folder = [
    pr ? `pr-${pr}` : `sha-${(env.GITHUB_SHA || '').slice(0, 7)}`,
    `${env.GITHUB_RUN_ID}-${env.GITHUB_RUN_ATTEMPT}`,
  ].join('/')

  const kinds = /** @type {const} */ (['expected', 'actual', 'diff'])
  const uploads = comparisons.flatMap((comparison, index) =>
    kinds.flatMap((kind) => {
      const file = comparison[kind]
      if (!file) return []
      return [{ comparison, file, kind, path: `${folder}/${index}-${slug(comparison.snapshot)}-${kind}.png` }]
    }),
  )

  const commit = await commitFiles(
    context,
    branch,
    uploads,
    `Visual check images for ${folder}`,
  )
  for (const upload of uploads) {
    const entry = urls.get(upload.comparison) || {}
    entry[upload.kind] = rawUrl(context, commit, upload.path)
    urls.set(upload.comparison, entry)
  }
  return urls
}

const report = async () => {
  const reportPath = input('REPORT')
  if (!fs.existsSync(reportPath)) {
    warn(`No Playwright report at ${reportPath}; skipping the visual check.`)
    return
  }

  const result = readReport(reportPath, input('ROOT_DIR') || undefined)
  const hasChanges = result.changed.length + result.added.length > 0

  /** @type {Map<Comparison, ImageUrls>} */
  let urls = new Map()
  try {
    urls = await uploadImages([...result.changed, ...result.added])
  } catch (error) {
    warn(`Could not upload images, so the check lists changes without them: ${error}`)
  }

  const output = renderOutput(result, urls, input('REPORT_URL') || undefined)
  writeSummary(`## ${input('CHECK_NAME')}\n\n${output.summary}\n\n${output.text}`)

  let checkUrl = ''
  try {
    checkUrl = await createCheckRun(context, {
      conclusion: hasChanges ? 'neutral' : 'success',
      detailsUrl: input('REPORT_URL') || undefined,
      headSha: input('HEAD_SHA'),
      name: input('CHECK_NAME'),
      output,
    })
  } catch (error) {
    warn(`Could not create the check run, so the results are in the job summary only: ${error}`)
  }

  setOutputs({
    'added': result.added.length,
    'changed': result.changed.length,
    'check-url': checkUrl,
    'total': result.total,
  })
}

const cleanup = async () => {
  const open = new Set((await listOpenPullRequests(context)).map((n) => `pr-${n}`))
  const { kept, removed } = await pruneBranch(context, branch, (path) =>
    open.has(path.split('/')[0]),
  )
  console.log(`Pruned ${branch}: kept ${kept} images, removed ${removed}.`)
}

const mode = input('MODE') || 'report'
if (mode === 'report') await report()
else if (mode === 'cleanup') await cleanup()
else throw new Error(`Unknown mode "${mode}": use "report" or "cleanup".`)
