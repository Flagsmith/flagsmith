import fetch from 'node-fetch';
import flagsmith from '@flagsmith/flagsmith/isomorphic';
import { IFlagsmith } from '@flagsmith/flagsmith/types';
import Project from '../../common/project';

export const LONG_TIMEOUT = 20000;
export const SHORT_TIMEOUT = 5000;

export const byId = (id: string) => `[data-test="${id}"]`;

// Logging functions
let currentSection = '';

export const log = (section?: string, message?: string) => {
  if (section) {
    currentSection = section;
    console.log(`\n[${section}]`);
  }
  if (message) {
    console.log(message);
  }
};

export const logUsingLastSection = (message: string) => {
  if (currentSection) {
    console.log(`[${currentSection}] ${message}`);
  } else {
    console.log(message);
  }
};

// Initialize Flagsmith once
const initProm = flagsmith.init({
  api: Project.flagsmithClientAPI,
  environmentID: Project.flagsmith,
  fetch,
});

export const getFlagsmith = async function (): Promise<IFlagsmith> {
  await initProm;
  return flagsmith as IFlagsmith;
};

// Whether the API under test is a SaaS deployment, per its `/version/` endpoint.
export const isSaas = async function (): Promise<boolean> {
  const api = process.env.FLAGSMITH_API_URL || Project.api;
  const res = await fetch(`${api.replace(/api\/v1\/$/, '')}version/`);
  const version = (await res.json()) as { is_saas?: boolean };
  return !!version.is_saas;
};
