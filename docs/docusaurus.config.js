import { themes as prismThemes } from 'prism-react-renderer';

/** @type {import('@docusaurus/types').Config} */
const config = {
    title: 'Flagsmith Docs',
    tagline: 'Open Source Feature Flags and Remote Config',
    url: 'https://docs.flagsmith.com',
    baseUrl: '/',
    favicon: 'img/favicon.ico',
    organizationName: 'Flagsmith',
    projectName: 'flagsmith',
    onBrokenLinks: 'throw',
    onBrokenMarkdownLinks: 'warn',

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
                    'json',
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
                content: `If you like Flagsmith, give us a star 🌟 on <a target="_blank" rel="noopener noreferrer" href="https://github.com/Flagsmith/flagsmith">GitHub</a> and follow us ❤️ on <a target="_blank" rel="noopener noreferrer" href="https://twitter.com/getflagsmith">Twitter</a>`,
                backgroundColor: '#5d60cc',
                textColor: '#ffffff',
                isCloseable: true,
            },
        }),

    i18n: {
        defaultLocale: 'en',
        locales: ['en'],
    },

    customFields: {
        swaggerURL: '/api-static/edge-api.yaml',
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
