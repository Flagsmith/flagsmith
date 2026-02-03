import { FullConfig } from '@playwright/test';

async function globalTeardown(config: FullConfig) {
  // Teardown logic here if needed in the future
}

export default globalTeardown;
