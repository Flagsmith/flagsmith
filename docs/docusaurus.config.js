/** @type {import('@docusaurus/types').DocusaurusConfig} */
module.exports = {
  baseUrl: '/',
  favicon: 'img/favicon.ico',
  i18n: {
    defaultLocale: 'en',
    localeConfigs: {
      en: {
        direction: 'ltr',
        label: 'English',
      },
    },
    locales: ['en'],
  },
  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',
  organizationName: 'Flagsmith',
  plugins: ['@ionic-internal/docusaurus-plugin-tag-manager'],
  presets: [
    [
      'docusaurus-preset-openapi',
      {
        api: {
          path: 'api_spec',
        },
        docs: {
          // Please change this to your repo.
          editUrl: 'https://github.com/flagsmith/flagsmith/tree/main/docs/',

          lastVersion: 'current',

          routeBasePath: '/',
          sidebarPath: require.resolve('./sidebars.js'),
          versions: {
            current: {
              badge: false,
              label: 'v2.0',
            },
            'v1.0': {
              badge: false,
              label: 'v1.0',
            },
          },
        },
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      },
    ],
  ],
  projectName: 'flagsmith',
  tagline: 'Open Source Feature Flags',
  themeConfig: {
    /*
        typesense: {
            typesenseCollectionName: 'flagsmith-docs',
            typesenseServerConfig: {
                apiKey: 'OY1ZDfWfrqSPcioQKuMP7hDd4o99BzKnhIVSOIP3nvn1GUih',
                nodes: [
                    {
                        host: 'typesense.flagsmith.com',
                        port: 443,
                        protocol: 'https',
                    },
                ],
            },
        },
        */
    algolia: {
      // Public API key: it is safe to commit it
      apiKey: '00987f2d774d7787dcae25294463294c',

      // The application ID provided by Algolia
      appId: 'GZAPCBLIEE',
      indexName: 'flagsmith',
    },

    announcementBar: {
      backgroundColor: '#5d60cc',
      content: `If you like Flagsmith, give us a star 🌟 on <a target="_blank" rel="noopener noreferrer" href="https://github.com/Flagsmith/flagsmith">GitHub</a> and follow us ❤️ on <a target="_blank" rel="noopener noreferrer" href="https://twitter.com/getflagsmith">Twitter</a>`,
      id: 'support_us',
      isCloseable: true,
      textColor: '#ffffff',
    },
    footer: {
      copyright: `Copyright © ${new Date().getFullYear()} Bullet Train Ltd. Built with Docusaurus.`,
      links: [
        {
          items: [
            {
              label: 'Flagsmith.com',
              to: 'https://flagsmith.com/',
            },
            {
              href: 'https://twitter.com/getflagsmith',
              label: 'Twitter',
            },
          ],
          title: 'Flagsmith',
        },
        {
          items: [
            {
              href: 'https://github.com/Flagsmith',
              label: 'Github',
            },
            {
              href: 'https://discord.gg/hFhxNtXzgm',
              label: 'Discord',
            },
          ],
          title: 'Open Source',
        },
        {
          items: [
            {
              label: 'Blog',
              to: 'https://flagsmith.com/blog/',
            },
            {
              href: 'https://flagsmith.com/podcast/',
              label: 'Podcast',
            },
          ],
          title: 'More',
        },
      ],
      style: 'dark',
    },
    navbar: {
      items: [
        {
          docId: 'intro',
          label: 'Docs',
          position: 'left',
          type: 'doc',
        },
        {
          label: 'API',
          position: 'left',
          to: '/api',
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
          href: 'https://discord.gg/hFhxNtXzgm',
          label: 'Discord',
          position: 'left',
        },
        {
          position: 'right',
          type: 'docsVersionDropdown',
        },
      ],
      logo: {
        alt: 'Flagsmith Logo',
        src: 'img/logo.svg',
      },
      title: 'Flagsmith',
    },
    prism: {
      additionalLanguages: [
        'java',
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
    tagManager: {
      trackingID: 'GTM-5ZV5K5G',
    },
  },
  title: 'Flagsmith Docs',
  url: 'https://docs.flagsmith.com',
}
