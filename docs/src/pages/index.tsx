import React from 'react';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import { IonIcon } from '@ionic/react';
import { 
  play,
  flag,
  cog,
  gitCompare,
  gitMerge,
  phonePortrait,
  server,
  codeWorking,
  extensionPuzzle,
  settings,
  cloudUpload,
  documentText,
  map,
} from 'ionicons/icons';
import styles from './index.module.css';

type CardProps = {
  title: string;
  description: string;
  link: string;
  icon?: any;
}

const Card: React.FC<CardProps> = ({ title, description, link, icon }) => (
  <div className={styles.card}>
    <div className="card-header flex-column">
      {icon && (
        <div className="icon-container">
          <IonIcon icon={icon} className="card-icon" />
        </div>
      )}
      <h3>{title}</h3>
    </div>
    <p>{description}</p>
    <Link to={link}>Learn more →</Link>
  </div>
);

type SectionProps = {
  title: string;
  children: React.ReactNode;
  id: string;
}

const Section: React.FC<SectionProps> = ({ title, children, id }) => (
  <section className={styles.section} data-section={id}>
    <h2>{title}</h2>
    <div className={styles.cardGrid}>{children}</div>
  </section>
);

const SECTIONS = [
  {
    title: "Introduction to Flagsmith",
    id: "introduction",
    cards: [
      {
        title: "Quickstart Guide",
        description: "Create your first project and flag",
        link: "/quickstart",
        icon: play
      },
      {
        title: "What are Feature Flags?",
        description: "Concepts and basics",
        link: "/basic-features/managing-features",
        icon: flag
      },
      {
        title: "Advanced Capabilities",
        description: "Testing, monitoring, analytics, experiments",
        link: "/advanced-use/ab-testing",
        icon: cog
      },
      {
        title: "Compare Plans",
        description: "Overview of Flagsmith plans",
        link: "/version-comparison",
        icon: gitCompare
      }
    ]
  },
  {
    title: "Flagsmith Integration",
    id: "integration",
    cards: [
      {
        title: "OpenFeature Compatibility",
        description: "Use Flagsmith with OpenFeature",
        link: "/clients/openfeature",
        icon: gitMerge
      },
      {
        title: "Client-Side SDKs",
        description: "Web, React Native, etc.",
        link: "/clients#client-side-sdks",
        icon: phonePortrait
      },
      {
        title: "Server-Side SDKs",
        description: "Node, Python, Java, etc.",
        link: "/clients#server-side-sdks",
        icon: server
      },
      {
        title: "Flagsmith API",
        description: "REST API reference and usage examples",
        link: "/clients/rest",
        icon: codeWorking
      }
    ]
  },
  {
    title: "Configuration & Deployment",
    id: "configuration",
    cards: [
      {
        title: "Integrations",
        description: "Third-party integrations (Segment, Datadog)",
        link: "/integrations",
        icon: extensionPuzzle
      },
      {
        title: "System Settings",
        description: "Admin settings and multi-tenancy",
        link: "/system-administration/authentication/",
        icon: settings
      },
      {
        title: "Self-hosting & Deployment",
        description: "Hosting options and setup",
        link: "/deployment",
        icon: cloudUpload
      }
    ]
  },
  {
    title: "Flagsmith Ecosystem",
    id: "ecosystem",
    cards: [
      {
        title: "Release Notes",
        description: "What's new in Flagsmith",
        link: "/platform/releases",
        icon: documentText
      },
      {
        title: "Public Roadmap",
        description: "Features coming soon",
        link: "/platform/roadmap",
        icon: map
      },
      {
        title: "Contribute to Flagsmith",
        description: "How to file issues, PRs, and contribute",
        link: "/CONTRIBUTING.md",
        icon: gitMerge
      }
    ]
  }
];

const Home: React.FC = () => (
  <Layout>
    <header className={styles.hero}>
      <div className="container">
        <div className={styles.heroInner}>
          <div>
            <h1>Manage feature flags and remote config across web, mobile, and server-side apps.</h1>
            <Link className="button button--primary button--lg" to="/docs/">
              Get Started
            </Link>
          </div>
          <img src="/img/full-logo.svg" alt="Flagsmith Logo" className={styles.logo} />
        </div>
      </div>
    </header>

    <main className="container">
      {SECTIONS.map(({ title, id, cards }) => (
        <Section key={id} title={title} id={id}>
          {cards.map((card, index) => (
            <Card key={`${id}-${index}`} {...card} />
          ))}
        </Section>
      ))}
    </main>
  </Layout>
);

export default Home;
