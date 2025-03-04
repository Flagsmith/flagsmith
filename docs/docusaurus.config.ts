// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

import type * as Preset from '@docusaurus/preset-classic';
import type { Config } from '@docusaurus/types';
import type * as Plugin from '@docusaurus/types/src/plugin';
import type * as OpenApiPlugin from 'docusaurus-plugin-openapi-docs';

const config: Config = {
    title: 'Flagsmith Docs',
    tagline: 'Open Source Feature Flags and Remote Config',
    url: 'https://docs.flagsmith.com',
    baseUrl: '/',
    favicon: 'img/favicon.ico',
    organizationName: 'Flagsmith',
    projectName: 'flagsmith',
    onBrokenLinks: 'throw',
    onBrokenMarkdownLinks: 'warn',

    markdown: {
        mermaid: true,
    },

    themes: ['@docusaurus/theme-mermaid', 'docusaurus-theme-openapi-docs'],

    presets: [
        [
            'classic',
            {
                docs: {
                    sidebarPath: require.resolve('./sidebars.ts'),
                    routeBasePath: '/', // Serve the docs at the site's root

                    // Please change this to your repo.
                    // Remove this to remove the "edit this page" links.
                    docItemComponent: '@theme/ApiItem', // Derived from docusaurus-theme-openapi
                },
                theme: {
                    customCss: require.resolve('./src/css/custom.css'),
                },
            } satisfies Preset.Options,
        ],
    ],

    themeConfig: {
        docs: {
            sidebar: {
                hideable: true,
            },
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
                    type: 'docSidebar',
                    sidebarId: 'tutorialSidebar',
                    position: 'left',
                    label: 'Docs',
                },
                {
                    label: 'Edge API Specification',
                    position: 'left',
                    to: '/edge-api/',
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
                            label: 'X',
                            href: 'https://x.com/getflagsmith',
                        },
                    ],
                },
                {
                    title: 'Open Source',
                    items: [
                        {
                            label: 'GitHub',
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
                        {
                            label: 'Status and Uptime',
                            href: 'https://status.flagsmith.com/',
                        },
                    ],
                },
                {
                    title: 'How-to guides',
                    items: [
                        {
                            label: '.NET',
                            href: 'https://www.flagsmith.com/blog/net-feature-flag',
                        },
                        {
                            label: 'Angular',
                            href: 'https://www.flagsmith.com/blog/angular-feature-flag',
                        },
                        {
                            label: 'Flutter',
                            href: 'https://www.flagsmith.com/blog/flutter-feature-flags',
                        },
                        {
                            label: 'Golang',
                            href: 'https://www.flagsmith.com/blog/golang-feature-flag',
                        },
                        {
                            label: 'Java',
                            href: 'https://www.flagsmith.com/blog/java-feature-toggle',
                        },
                        {
                            label: 'JavaScript',
                            href: 'https://www.flagsmith.com/blog/javascript-feature-flags',
                        },
                        {
                            label: 'Kotlin/Android',
                            href: 'https://www.flagsmith.com/blog/feature-flags-android',
                        },
                        {
                            label: 'Node.js',
                            href: 'https://www.flagsmith.com/blog/nodejs-feature-flags',
                        },
                        {
                            label: 'PHP',
                            href: 'https://www.flagsmith.com/blog/php-feature-flags',
                        },
                        {
                            label: 'Python',
                            href: 'https://www.flagsmith.com/blog/python-feature-flag',
                        },
                        {
                            label: 'React Native',
                            href: 'https://www.flagsmith.com/blog/update-your-react-native-app-using-remote-config',
                        },
                        {
                            label: 'Ruby',
                            href: 'https://www.flagsmith.com/blog/ruby-feature-flags',
                        },
                        {
                            label: 'Spring Boot',
                            href: 'https://www.flagsmith.com/blog/spring-boot-feature-flags',
                        },
                        {
                            label: 'Swift/iOS',
                            href: 'https://www.flagsmith.com/blog/swift-ios-feature-flags',
                        },
                    ],
                },
            ],
            copyright: `Copyright © ${new Date().getFullYear()} Bullet Train Ltd. Built with Docusaurus.`,
        },
        announcementBar: {
            id: 'support_us',
            content: `If you like Flagsmith, give us a star 🌟 on <a target="_blank" rel="noopener noreferrer" href="https://github.com/Flagsmith/flagsmith">GitHub</a> and follow us ❤️ on <a target="_blank" rel="noopener noreferrer" href="https://x.com/getflagsmith">X</a>`,
            backgroundColor: '#5d60cc',
            textColor: '#ffffff',
            isCloseable: true,
        },
        prism: {
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
                'json',
            ],
        },
        languageTabs: [
            {
                highlight: 'python',
                language: 'python',
                logoClass: 'python',
            },
            {
                highlight: 'bash',
                language: 'curl',
                logoClass: 'bash',
            },
            {
                highlight: 'csharp',
                language: 'csharp',
                logoClass: 'csharp',
            },
            {
                highlight: 'go',
                language: 'go',
                logoClass: 'go',
            },
            {
                highlight: 'javascript',
                language: 'nodejs',
                logoClass: 'nodejs',
            },
            {
                highlight: 'ruby',
                language: 'ruby',
                logoClass: 'ruby',
            },
            {
                highlight: 'php',
                language: 'php',
                logoClass: 'php',
            },
            {
                highlight: 'java',
                language: 'java',
                logoClass: 'java',
                variant: 'unirest',
            },
            {
                highlight: 'powershell',
                language: 'powershell',
                logoClass: 'powershell',
            },
        ],
    } satisfies Preset.ThemeConfig,

    customFields: {
        CI: process.env.CI,
    },

    plugins: [
        './plugins/flagsmith-versions',
        [
            'docusaurus-plugin-openapi-docs',
            {
                id: 'openapi',
                docsPluginId: 'classic',
                config: {
                    partner: {
                        specPath: 'static/openapi/edge-api.yaml',
                        outputDir: 'docs/edge-api',
                        sidebarOptions: {
                            groupPathsBy: 'tag',
                            categoryLinkSource: 'tag',
                        },
                    } satisfies OpenApiPlugin.Options,
                } satisfies Plugin.PluginOptions,
            },
        ],
    ],

    scripts: [
        '/js/crisp-chat.js',
        {
            src: '//js-eu1.hs-scripts.com/143451822.js',
            async: true,
            defer: true,
            id: 'hs-script-loader',
        },
    ],

    clientModules: [
        require.resolve('./plugins/crisp-chat-links.js'),
        require.resolve('./plugins/reo.js'),
    ],
};

export default async function createConfig() {
    return config;
}
