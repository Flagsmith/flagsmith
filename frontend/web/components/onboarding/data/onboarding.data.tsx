export type Resource = {
  description: string
  image: string
  title: string
  url: string
}

type LinkItem = {
  title: string
  href: string
}

export const resources: Resource[] = [
  {
    'description':
      'A hands-on guide covering best practices, use cases and more.',
    'image': '/static/images/welcome/featured1.png',
    'title': 'eBook | Unlock Modern Software Development with Feature Flags',
    url: 'https://www.flagsmith.com/ebook/flip-the-switch-on-modern-software-development-with-feature-flags?utm_source=app',
  },
  {
    'description': 'Set yourself up for success with these best practices.',
    'image': '/static/images/welcome/featured2.png',
    'title': 'Blog Post | Feature Flag best practices',
    url: 'https://www.flagsmith.com/blog/feature-flags-best-practices?utm_source=app',
  },
]

export const links: LinkItem[] = [
  {
    href: 'https://github.com/flagsmith',
    title: 'Find us on GitHub',
  },
  {
    href: 'https://docs.flagsmith.com/platform/contributing',
    title: 'Contribution Guidelines',
  },
  {
    href: 'https://discord.gg/hFhxNtXzgm',
    title: 'Chat with Developers on Discord',
  },
  {
    href: 'https://www.flagsmith.com/blog',
    title: 'View our Blog',
  },
  {
    href: 'https://www.flagsmith.com/podcast',
    title: 'Listen to our Podcast',
  },
]
