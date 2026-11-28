'use strict';

const fs = require('fs');
const path = require('path');
const cheerio = require('cheerio');
const TurndownService = require('turndown');
const { gfm } = require('turndown-plugin-gfm');

const SUMMARY =
    'Documentation for the Flagsmith feature flag service, written for developers and AI agents. Every page is available as Markdown. Append `.md` to any page URL to get it.';

const DIRECTIVE =
    '> The full documentation index for AI agents is [llms.txt](https://docs.flagsmith.com/llms.txt). Append `.md` to any page URL to get the Markdown version.';

const turndown = new TurndownService({
    headingStyle: 'atx',
    codeBlockStyle: 'fenced',
    bulletListMarker: '-',
});
turndown.use(gfm);

function listHtmlFiles(directory, files = []) {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
        const entryPath = path.join(directory, entry.name);
        if (entry.isDirectory()) {
            listHtmlFiles(entryPath, files);
        } else if (entry.isFile() && entry.name.endsWith('.html')) {
            files.push(entryPath);
        }
    }
    return files;
}

function markdownPathFromHtml(relativePath) {
    const normalized = relativePath.split(path.sep).join('/');
    if (normalized === 'index.html') {
        return 'index.md';
    }
    if (normalized.endsWith('/index.html')) {
        return `${normalized.slice(0, -'/index.html'.length)}.md`;
    }
    if (normalized.endsWith('.html')) {
        return `${normalized.slice(0, -'.html'.length)}.md`;
    }
    return null;
}

function labelFromMarkdownPath(markdownPath) {
    const segments = markdownPath.split('/').filter(Boolean);
    if (segments.length <= 1) {
        return 'Overview';
    }
    return segments[0]
        .split('-')
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

function cleanText(value) {
    return value.replace(/\s+/g, ' ').trim();
}

function convertHtml(html) {
    const $ = cheerio.load(html);
    const content = $('.theme-doc-markdown').first();
    const source = content.length ? content : $('article').first();
    if (!source.length) {
        return null;
    }

    source.find('script, style, button, .hash-link').remove();
    source.find('img[src^="data:"], source[src^="data:"]').each((_, element) => {
        $(element).replaceWith($(element).attr('alt') ?? '');
    });
    const sourceHtml = source.html();
    if (!sourceHtml) {
        return null;
    }

    const body = turndown.turndown(sourceHtml).trim();
    if (!body) {
        return null;
    }

    const title = cleanText(content.find('h1').first().text() || $('article h1').first().text() || $('title').text());

    return {
        title,
        markdown: `${DIRECTIVE}\n\n${body}\n`,
    };
}

module.exports = function agentLlms(context) {
    const siteUrl = String(context.siteConfig.url || '').replace(/\/$/, '');

    return {
        name: 'agent-llms',
        postBuild({ outDir }) {
            const root = path.resolve(outDir);
            const pages = [];

            for (const file of listHtmlFiles(root)) {
                if (path.basename(file) === '404.html') {
                    continue;
                }

                const markdownPath = markdownPathFromHtml(path.relative(root, file));
                if (!markdownPath) {
                    continue;
                }

                const converted = convertHtml(fs.readFileSync(file, 'utf8'));
                if (!converted || !converted.title) {
                    continue;
                }

                const outputPath = path.join(root, markdownPath);
                fs.mkdirSync(path.dirname(outputPath), { recursive: true });
                fs.writeFileSync(outputPath, converted.markdown, 'utf8');
                pages.push({ title: converted.title, markdownPath });
            }

            const categories = new Map();
            for (const page of pages) {
                const label = labelFromMarkdownPath(page.markdownPath);
                if (!categories.has(label)) {
                    categories.set(label, []);
                }
                categories.get(label).push(page);
            }

            const lines = ['# Flagsmith documentation', '', `> ${SUMMARY}`, ''];

            for (const label of [...categories.keys()].sort()) {
                lines.push(`## ${label}`, '');
                const entries = categories.get(label).sort((a, b) => a.title.localeCompare(b.title));
                for (const entry of entries) {
                    const title = entry.title.replace(/[[\]]/g, '');
                    lines.push(`- [${title}](${siteUrl}/${entry.markdownPath})`);
                }
                lines.push('');
            }

            fs.writeFileSync(path.join(root, 'llms.txt'), `${lines.join('\n')}\n`, 'utf8');
            console.log(`[agent-llms] Wrote ${pages.length} Markdown files and llms.txt`);
        },
    };
};
