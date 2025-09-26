import React from 'react';
import clsx from 'clsx';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import { IonIcon } from '@ionic/react';
import { 
    play,
    flag,
    analytics,
    layers,
    gitMerge,
    phonePortrait,
    server,
    codeWorking,
    extensionPuzzle,
    settings,
    cloudUpload,
    documentText,
    map,
    gitBranch,
    construct,
    cog,
} from 'ionicons/icons';
import styles from './index.module.css';

function Card({ title, description, link, icon }) {
  return (
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
}

function Section({ title, children, id }) {
  return (
    <section className={styles.section} data-section={id}>
      <h2>{title}</h2>
      <div className={styles.cardGrid}>{children}</div>
    </section>
  );
}

export default function Home() {
  return (
    <Layout>
      <header className={styles.hero}>
        <div className="container">
          <div className={styles.heroInner}>
            <div>
              <h1>Manage feature flags and remote config across web, mobile, and server-side apps.</h1>
              <Link className="button button--primary button--lg" to="/getting-started/feature-flags">
                Get Started
              </Link>
            </div>
            <img src="/img/full-logo.svg" alt="Flagsmith Logo" className={styles.logo} />
          </div>
        </div>
      </header>

      <main className="container">
        <Section title="Introduction to Flagsmith" id="introduction">
          <Card 
            title="Quickstart Guide" 
            description="Create your first project and flag" 
            link="/getting-started/quick-start"
            icon={play} 
          />
          <Card 
            title="What are Feature Flags?" 
            description="Concepts and basics" 
            link="/getting-started/feature-flags"
            icon={flag} 
          />
          <Card 
            title="Platform Architecture" 
            description="How Flagsmith works and components" 
            link="/flagsmith-concepts/platform-architecture"
            icon={construct} 
          />
          <Card 
            title="Basic Flag Management" 
            description="Create, edit, and manage your first flags" 
            link="/managing-flags/core-management"
            icon={cog} 
          />
        </Section>

        <Section title="Flagsmith Integration" id="integration">
          <Card 
            title="OpenFeature Compatibility" 
            description="Use Flagsmith with OpenFeature" 
            link="/flagsmith-integration/openfeature/"
            icon={gitMerge} 
          />
          <Card 
            title="Client-Side SDKs" 
            description="Web, React Native, etc." 
            link="/flagsmith-integration/integration-overview/"
            icon={phonePortrait} 
          />
          <Card 
            title="Server-Side SDKs" 
            description="Node, Python, Java, etc." 
            link="/flagsmith-integration/server-side"
            icon={server} 
          />
          <Card 
            title="Flagsmith API" 
            description="REST API reference and usage examples" 
            link="/flagsmith-integration/flagsmith-api-overview/"
            icon={codeWorking} 
          />
        </Section>

        <Section title="Configuration & Deployment" id="configuration">
          <Card 
            title="Integrations" 
            description="Integrations with third-party observability, analytics and other platforms" 
            link="/third-party-integrations"
            icon={extensionPuzzle} 
          />
          <Card 
            title="Platform Administration" 
            description="Authentication, permissions and platform configuration" 
            link="/administration-and-security/"
            icon={settings} 
          />
          <Card 
            title="Self-hosting & Deployment" 
            description="Hosting options and set up" 
            link="/deployment-self-hosting/"
            icon={cloudUpload} 
          />
        </Section>

        <Section title="Flagsmith Ecosystem" id="ecosystem">
          <Card 
            title="Release Notes" 
            description="What's new in Flagsmith" 
            link="/project-and-community/release-notes/"
            icon={documentText} 
          />
          <Card 
            title="Public Roadmap" 
            description="Features coming soon" 
            link="/project-and-community/roadmap/"
            icon={map} 
          />
          <Card 
            title="Contribute to Flagsmith" 
            description="How to file issues, PRs, and contribute" 
            link="/project-and-community/contributing/"
            icon={gitBranch} 
          />
        </Section>
      </main>
    </Layout>
  );
}
