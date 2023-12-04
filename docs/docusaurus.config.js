// @ts-check
// `@type` JSDoc annotations allow editor autocompletion and type checking
// (when paired with `@ts-check`).
// There are various equivalent ways to declare your Docusaurus config.
// See: https://docusaurus.io/docs/api/docusaurus-config

import { themes as prismThemes } from 'prism-react-renderer';

/** @type {import('@docusaurus/types').Config} */
const config = {
    title: 'Flagsmith Docs',
    tagline: 'Open Source Feature Flags',
    url: 'https://docs.flagsmith.com',
    baseUrl: '/',
    favicon: 'img/favicon.ico',
    organizationName: 'Flagsmith',
    projectName: 'flagsmith',
    onBrokenLinks: 'throw',
    onBrokenMarkdownLinks: 'warn',
    plugins: ['@ionic-internal/docusaurus-plugin-tag-manager'],
    themeConfig:
        /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
        ({
            prism: {
                theme: prismThemes.github,
                darkTheme: prismThemes.dracula,
                additionalLanguages: [
                    'java',
                    'scala',
                    'csharp',
                    'ruby',
                    'rust',
                    'swift',
                    'dart',
                    'php',
                    'kotlin',
                    'groovy',
                    'hcl',
                ],
            },
            algolia: {
                // The application ID provided by Algolia
                appId: 'GZAPCBLIEE',
                // Public API key: it is safe to commit it
                apiKey: '00987f2d774d7787dcae25294463294c',
                indexName: 'flagsmith',
            },
            tagManager: {
                trackingID: 'GTM-5ZV5K5G',
            },
            navbar: {
                title: 'Flagsmith',
                logo: {
                    alt: 'Flagsmith Logo',
                    src: 'img/logo.svg',
                },
                items: [
                    {
                        type: 'doc',
                        docId: 'intro',
                        position: 'left',
                        label: 'Docs',
                    },
                    {
                        to: '/api',
                        label: 'API',
                        position: 'left',
                    },
                    {
                        href: 'https://flagsmith.com',
                        label: 'Flagsmith.com',
                        position: 'left',
                    },
                    {
                        href: 'https://github.com/flagsmith/flagsmith',
                        label: 'GitHub',
                        position: 'left',
                    },
                    {
                        label: 'Discord',
                        href: 'https://discord.gg/hFhxNtXzgm',
                        position: 'left',
                    },
                ],
            },
            footer: {
                style: 'dark',
                links: [
                    {
                        title: 'Flagsmith',
                        items: [
                            {
                                label: 'Flagsmith.com',
                                to: 'https://flagsmith.com/',
                            },
                            {
                                label: 'Twitter',
                                href: 'https://twitter.com/getflagsmith',
                            },
                        ],
                    },
                    {
                        title: 'Open Source',
                        items: [
                            {
                                label: 'Github',
                                href: 'https://github.com/Flagsmith',
                            },
                            {
                                label: 'Discord',
                                href: 'https://discord.gg/hFhxNtXzgm',
                            },
                        ],
                    },
                    {
                        title: 'More',
                        items: [
                            {
                                label: 'Blog',
                                to: 'https://flagsmith.com/blog/',
                            },
                            {
                                label: 'Podcast',
                                href: 'https://flagsmith.com/podcast/',
                            },
                        ],
                    },
                ],
                copyright: `Copyright © ${new Date().getFullYear()} Bullet Train Ltd. Built with Docusaurus.`,
            },
            announcementBar: {
                id: 'support_us',
                content: `If you like Flagsmith, give us a star 🌟 on <a target="_blank" rel="noopener noreferrer" href="https://github.com/Flagsmith/flagsmith">GitHub</a> and follow us ❤️ on <a target="_blank" rel="noopener noreferrer" href="https://twitter.com/getflagsmith">Twitter</a>`,
                backgroundColor: '#5d60cc',
                textColor: '#ffffff',
                isCloseable: true,
            },
        }),
    // Even if you don't use internationalization, you can use this field to set
    // useful metadata like html lang. For example, if your site is Chinese, you
    // may want to replace "en" with "zh-Hans".
    i18n: {
        defaultLocale: 'en',
        locales: ['en'],
    },

    customFields: {
        swaggerURL: 'https://raw.githubusercontent.com/dabeeeenster/api-spec/main/edge_api.json',
    },

    presets: [
        [
            'classic',
            /** @type {import('@docusaurus/preset-classic').Options} */
            ({
                docs: {
                    sidebarPath: require.resolve('./sidebars.js'),
                    routeBasePath: '/',
                    // Please change this to your repo.
                    editUrl: 'https://github.com/flagsmith/flagsmith/tree/main/docs/',
                },
                theme: {
                    customCss: './src/css/custom.css',
                },
            }),
        ],
    ],
};

export default config;
