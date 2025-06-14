---
sidebar_position: 3
---

import Card from '@site/src/components/Card';
import CardHeader from '@site/src/components/Card/CardHeader';
import CardBody from '@site/src/components/Card/CardBody';
import CardFooter from '@site/src/components/Card/CardFooter';

# Version Comparison

Choose the right Flagsmith version for your needs. Compare our Open Source, SaaS, and Enterprise offerings:

## Feature Comparison

|  | Free | Saas | Enterprise |
|---------|:-------------:|:------:|:------------:|
| **Core Features** |
| Feature Flags | ✅ | ✅ | ✅ |
| Remote Config | ✅ | ✅ | ✅ |
| User Segments | ✅ | ✅ | ✅ |
| A/B Testing | ✅ | ✅ | ✅ |
| 3rd Party Integrations | ✅ | ✅ | ✅ |
| **Scaling** |
| API Request Limits | 50k/month | 1M/month | 5M+/month |
| Team Members | 1 | 3 | 20+ |
| Projects | Single | Unlimited | Unlimited |
| Environments | Unlimited | Unlimited | Unlimited |
| **Advanced Features** |
| Change Requests | ❌ | ✅ | ✅ |
| Flag Scheduling | ❌ | ✅ | ✅ |
| Role-Based Access Control | ❌ | ✅ | ✅ |
| Audit Logs | ❌ | ✅ | ✅ |
| Two-Factor Authentication | ❌ | ✅ | ✅ |
| Priority Support | ❌ | Email | Slack/Discord |
| **Enterprise Features** |
| Custom SLA | ❌ | ❌ | ✅ |
| On-Boarding and Training | ❌ | ❌ | ✅ |
| Custom Fields | ❌ | ❌ | ✅ |
| **Authentication** |
| Email/Password | ✅ | ✅ | ✅ |
| OAuth | ✅ | ✅ | ✅ |
| SAML/SSO | ❌ | ❌ | ✅ |
| LDAP | ❌ | ❌ | ✅ |
| Okta | ❌ | ❌ | ✅ |
| **Infrastructure** |
| Self-hosted | ✅ | ❌ | Optional |
| Cloud Hosted | ❌ | ✅ | Optional |
| Private Cloud | ❌ | ❌ | ✅ |
| Edge API | ❌ | ✅ | Optional |
| Database Options | PostgreSQL | PostgreSQL | PostgreSQL, Oracle, MySQL |

## Deployment Options

<div className="row">
  <div className="col col--4">
    <Card>
      <CardHeader>
        <h3>🚀 Free </h3>
      </CardHeader>
      <CardBody>
        <ul>
          <li>Up to 50,000 Requests/Month</li>
          <li>1 Team Member</li>
          <li>Unlimited Feature Flags</li>
          <li>Unlimited Environments</li>
          <li>A/B and MVT Testing</li>
          <li>API Access</li>
        </ul>
      </CardBody>
      <CardFooter>
        <a href="/deployment" className="button button--primary button--sm">
          View Deployment Guide
        </a>
      </CardFooter>
    </Card>
  </div>
  
  <div className="col col--4">
    <Card>  
      <CardHeader>
        <h3>☁️ Start-Up</h3>
      </CardHeader>
      <CardBody>
        <ul>
          <li>Up to 1,000,000 Requests/Month</li>
          <li>3 Team Members</li>
          <li>Unlimited Projects</li>
          <li>Email Technical Support</li>
          <li>Scheduled Flags</li>
          <li>Global Edge API</li>
        </ul>
      </CardBody>
      <CardFooter>
        <a href="https://app.flagsmith.com/signup" className="button button--primary button--sm">
          Start Free Trial
        </a>
      </CardFooter>
    </Card>
  </div>

  <div className="col col--4">
    <Card>
      <CardHeader>
        <h3>🏢 Enterprise</h3>
      </CardHeader>
      <CardBody>
        <ul>
          <li>5,000,000+ Requests/Month</li>
          <li>20+ Team Members</li>
          <li>Advanced Hosting Options</li>
          <li>Priority Support via Slack/Discord</li>
          <li>Custom SLA</li>
        </ul>
      </CardBody>
      <CardFooter>
        <a href="https://flagsmith.com/contact-us" className="button button--primary button--sm">
          Contact Sales
        </a>
      </CardFooter>
    </Card>
  </div>
</div>

:::tip Migration
You can easily switch between SaaS and Self Hosted Flagsmith using our [Import and Export tools](system-administration/importing-and-exporting/organisations).
:::
