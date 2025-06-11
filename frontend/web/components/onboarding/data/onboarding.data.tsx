import { ImgHTMLAttributes } from 'react'

export type Resource = {
  description: string
  image: Partial<ImgHTMLAttributes<any>>
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
      'Move faster while improving safety, fight vendor lock-in, and how global organisations like eBay use feature flags at scale.',
    'image': {
      src: 'https://cdn.prod.website-files.com/645258eae17c724fb2ca4915/682f63f56c99f14170876b92_Cover.png',
      srcSet:
        'https://cdn.prod.website-files.com/645258eae17c724fb2ca4915/682f63f56c99f14170876b92_Cover-p-500.png 500w, https://cdn.prod.website-files.com/645258eae17c724fb2ca4915/682f63f56c99f14170876b92_Cover-p-800.png 800w, https://cdn.prod.website-files.com/645258eae17c724fb2ca4915/682f63f56c99f14170876b92_Cover-p-1080.png 1080w, https://cdn.prod.website-files.com/645258eae17c724fb2ca4915/682f63f56c99f14170876b92_Cover.png 1224w',
    },
    'title': 'eBook | Scaling Feature Flags',
    url: 'https://www.flagsmith.com/ebook/scaling-feature-flags-a-roadmap?utm_source=app',
  },
  {
    'description': 'Set yourself up for success with these best practices.',
    'image': {
      src: 'https://cdn.prod.website-files.com/645258eae17c724fb2ca4915/67fff41c071081c1a18d7102_Feature%20Flags%20Best%20Practices%20Article%20Header.png',
      srcSet:
        'https://cdn.prod.website-files.com/645258eae17c724fb2ca4915/67fff41c071081c1a18d7102_Feature%20Flags%20Best%20Practices%20Article%20Header-p-500.png 500w, https://cdn.prod.website-files.com/645258eae17c724fb2ca4915/67fff41c071081c1a18d7102_Feature%20Flags%20Best%20Practices%20Article%20Header-p-800.png 800w, https://cdn.prod.website-files.com/645258eae17c724fb2ca4915/67fff41c071081c1a18d7102_Feature%20Flags%20Best%20Practices%20Article%20Header-p-1080.png 1080w, https://cdn.prod.website-files.com/645258eae17c724fb2ca4915/67fff41c071081c1a18d7102_Feature%20Flags%20Best%20Practices%20Article%20Header-p-1600.png 1600w, https://cdn.prod.website-files.com/645258eae17c724fb2ca4915/67fff41c071081c1a18d7102_Feature%20Flags%20Best%20Practices%20Article%20Header-p-2000.png 2000w, https://cdn.prod.website-files.com/645258eae17c724fb2ca4915/67fff41c071081c1a18d7102_Feature%20Flags%20Best%20Practices%20Article%20Header.png 2400w',
    },
    'title': 'Blog Post | Feature Flag best practices',
    url: 'https://www.flagsmith.com/blog/feature-flags-best-practices?utm_source=app',
  },
  {
    'description':
      'A hands-on guide covering best practices, use cases and more.',
    'image': {
      src: 'https://cdn.prod.website-files.com/645258eae17c724fb2ca4915/673b280d0c8c9a9b1d58ee63_modern-software-development.webp',
    },
    'title': 'eBook | Unlock Modern Software Development with Feature Flags',
    url: 'https://www.flagsmith.com/ebook/flip-the-switch-on-modern-software-development-with-feature-flags?utm_source=app',
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
