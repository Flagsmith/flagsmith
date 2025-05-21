import React from 'react';
import clsx from 'clsx';
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
    gitBranch,
} from 'ionicons/icons';
import styles from './index.module.css';
// TODO - Replace placeholder image with actual logo
// TODO - Allign hero with sections
// TODO - Icon must be above card title
// TODO - Fix card per line: 2x2 first 1x4 second etc
// TODO - Responsiveness
// TODO - Hero/header spacing (logo and text)
// TODO - Icon circle has a different color than the card background in light mode
// TODO - fix alternating background (must change every 2 sections)
// TODO - Hover para link da card
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

function Section({ title, children }) {
  return (
    <section className={styles.section}>
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
              <Link className="button button--primary button--lg" to="/docs/">
                Get Started
              </Link>
            </div>
            <img src="/img/banner-logo-dark.png" alt="Flagsmith Logo" className={styles.logo} /> {/* Placeholder img needs replacement */}
          </div>
        </div>
      </header>

      <main className="container">
        <Section title="Introduction to Flagsmith">
          <Card 
            title="Quickstart Guide" 
            description="Create your first project and flag" 
            link="/quickstart"
            icon={play} 
          />
          <Card 
            title="What are Feature Flags?" 
            description="Concepts and basics" 
            link="/basic-features/managing-features"
            icon={flag} 
          />
          <Card 
            title="Advanced Capabilities" 
            description="Testing, monitoring, analytics, experiments" 
            link="/advanced-use/ab-testing"
            icon={cog} 
          />
          <Card 
            title="Compare Plans" 
            description="Overview of Flagsmith plans" 
            link="/version-comparison"
            icon={gitCompare} 
          />
        </Section>

        <Section title="Flagsmith Integration">
          <Card 
            title="OpenFeature Compatibility" 
            description="Use Flagsmith with OpenFeature" 
            link="/clients/openfeature"
            icon={gitMerge} 
          />
          <Card 
            title="Client-Side SDKs" 
            description="Web, React Native, etc." 
            link="/clients#client-side-sdks"
            icon={phonePortrait} 
          />
          <Card 
            title="Server-Side SDKs" 
            description="Node, Python, Java, etc." 
            link="/clients#server-side-sdks"
            icon={server} 
          />
          <Card 
            title="Flagsmith API" 
            description="REST API reference and usage examples" 
            link="/clients/rest"
            icon={codeWorking} 
          />
        </Section>

        <Section title="Configuration & Deployment">
          <Card 
            title="Integrations" 
            description="Third-party integrations (Segment, Datadog)" 
            link="/integrations"
            icon={extensionPuzzle} 
          />
          <Card 
            title="System Settings" 
            description="Admin settings and multi-tenancy" 
            link="/system-administration/authentication/"
            icon={settings} 
          /> {/*Placeholder until this section has a index*/}
          <Card 
            title="Self-hosting & Deployment" 
            description="Hosting options and setup" 
            link="/deployment"
            icon={cloudUpload} 
          />
        </Section>

        <Section title="Flagsmith Ecosystem">
          <Card 
            title="Release Notes" 
            description="What's new in Flagsmith" 
            link="/platform/releases"
            icon={documentText} 
          />
          <Card 
            title="Public Roadmap" 
            description="Features coming soon" 
            link="/platform/roadmap"
            icon={map} 
          />
          <Card 
            title="Contribute to Flagsmith" 
            description="How to file issues, PRs, and contribute" 
            link="/CONTRIBUTING.md"
            icon={gitMerge} 
          />
        </Section>
      </main>
    </Layout>
  );
}
