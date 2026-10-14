// @ts-check

/**
 * @typedef {import('./report.mjs').Comparison} Comparison
 * @typedef {import('./report.mjs').VisualResult} VisualResult
 * @typedef {{ expected?: string, actual?: string, diff?: string }} ImageUrls
 */

// GitHub rejects check run output fields over 65535 characters.
const MAX_TEXT = 60000
// Open each change by default only while the page stays short.
const MAX_OPEN = 3

/** @param {VisualResult} result */
export const renderTitle = ({ added, changed, total }) => {
  if (!changed.length && !added.length) {
    return `No visual changes (${total} compared)`
  }
  const parts = []
  if (changed.length) parts.push(`${changed.length} changed`)
  if (added.length) parts.push(`${added.length} new`)
  return `${parts.join(', ')} of ${total}`
}

/** @param {string} value */
const escape = (value) =>
  value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

/** @param {string | undefined} url @param {string} alt */
const image = (url, alt) =>
  url ? `<a href="${url}"><img src="${url}" alt="${alt}" width="100%"></a>` : '–'

/** @param {Comparison} comparison */
const describe = ({ file, pixels, ratio, snapshot }) => {
  const details = [escape(file), escape(snapshot)]
  if (pixels !== undefined) {
    details.push(`${pixels.toLocaleString('en-GB')} px differ (${ratio})`)
  }
  return details.join(' · ')
}

/**
 * @param {Comparison} comparison
 * @param {ImageUrls | undefined} urls
 * @param {boolean} open
 */
const renderChange = (comparison, urls, open) => {
  const table = urls
    ? [
        '| Before | After | Diff |',
        '| --- | --- | --- |',
        `| ${image(urls.expected, 'Before')} | ${image(urls.actual, 'After')} | ${image(urls.diff, 'Diff')} |`,
      ].join('\n')
    : '_Images unavailable: see the full report._'
  return [
    `<details${open ? ' open' : ''}><summary><strong>${escape(comparison.title)}</strong></summary>`,
    '',
    `<sub>${describe(comparison)}</sub>`,
    '',
    table,
    '',
    '</details>',
  ].join('\n')
}

/**
 * @param {Comparison} comparison
 * @param {ImageUrls | undefined} urls
 */
const renderAdded = (comparison, urls) =>
  [
    `<details><summary><strong>${escape(comparison.title)}</strong> (no baseline)</summary>`,
    '',
    `<sub>${describe(comparison)}</sub>`,
    '',
    urls?.actual ? image(urls.actual, 'New') : '_Image unavailable._',
    '',
    '</details>',
  ].join('\n')

/**
 * @param {VisualResult} result
 * @param {Map<Comparison, ImageUrls>} urls
 * @param {string} [reportUrl]
 */
export const renderOutput = (result, urls, reportUrl) => {
  const title = renderTitle(result)
  const unchanged = result.total - result.changed.length - result.added.length
  const summary = [
    `**${title}**`,
    '',
    `${unchanged} unchanged · ${result.changed.length} changed · ${result.added.length} new`,
    reportUrl ? `\n[Full Playwright report](${reportUrl})` : '',
  ].join('\n')

  const open = result.changed.length <= MAX_OPEN
  const sections = [
    ...result.changed.map((c) => renderChange(c, urls.get(c), open)),
    ...result.added.map((c) => renderAdded(c, urls.get(c))),
  ]

  let text = ''
  for (const [index, section] of sections.entries()) {
    if (text.length + section.length > MAX_TEXT) {
      text += `\n\n…and ${sections.length - index} more, see the full report.`
      break
    }
    text += (text ? '\n\n' : '') + section
  }

  return { summary, text, title }
}
