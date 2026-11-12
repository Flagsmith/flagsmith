import { Page } from '@playwright/test';

// Map of status codes to URL patterns that should be ignored in logs
const IGNORE_RESPONSE_ERRORS: Record<number, string[]> = {
  404: [
    '/usage-data/', // Expected for new orgs without billing
    '/list-change-requests/', // Enterprise feature, expected in OSS
    '/change-requests/', // Enterprise feature, expected in OSS
    '/release-pipelines/', // Enterprise feature, expected in OSS
    '/roles/', // May not exist in certain configurations
    '/saml/configuration/', // Enterprise feature, expected in OSS
  ],
  403: [
    '/get-subscription-metadata/', // Expected for non-admin users
    '/usage-data/', // Expected for non-admin users
    '/invite-links/', // Expected for non-admin users
    '/roles/', // Expected for non-admin users
    '/change-requests/', // Expected for non-admin users
    '/api-keys/', // Expected for non-admin users
    '/metrics/', // Expected for non-admin users
    '/invites/', // Expected for non-admin users
  ],
  429: [
    '/usage-data/', // Usage data endpoint has rate limiting, throttling is expected
  ],
};

// Browser debugging - console and network logging
export const setupBrowserLogging = (page: Page) => {
  // Track console messages
  page.on('console', async (msg) => {
    const type = msg.type();
    const text = msg.text();

    // Only log errors and warnings
    if (type === 'error') {
      console.error('\n🔴 [CONSOLE ERROR]', text);
      // Try to get stack trace if available
      const args = msg.args();
      for (const arg of args) {
        try {
          const val = await arg.jsonValue();
          if (val && typeof val === 'object' && val.stack) {
            console.error('  Stack:', val.stack);
          }
        } catch (e) {
          // Ignore if we can't get the value
        }
      }
    } else if (type === 'warning') {
      // Disabled to reduce noise
      // console.warn('\n🟡 [CONSOLE WARNING]', text);
    }
  });

  // Track page errors
  page.on('pageerror', (error) => {
    console.error('\n🔴 [PAGE ERROR]', error.message);
    if (error.stack) {
      console.error('  Stack:', error.stack);
    }
  });

  // Track failed network requests
  page.on('requestfailed', (request) => {
    const url = request.url();
    const failure = request.failure();
    console.error('\n🔴 [NETWORK FAILED]', request.method(), url);
    if (failure) {
      console.error('  Error:', failure.errorText);
    }
  });

  // Track API responses with errors
  page.on('response', async (response) => {
    const url = response.url();
    const status = response.status();

    // Only log API calls (not static assets)
    if (!url.includes('/api/') && !url.includes('/e2etests/')) {
      return;
    }

    // Ignore false positive errors that are expected/harmless
    const ignoreUrls = IGNORE_RESPONSE_ERRORS[status];
    if (ignoreUrls && ignoreUrls.some(pattern => url.includes(pattern))) {
      return;
    }

    // Log throttling, rate limiting, and server errors
    if (status === 429) {
      console.error('\n🔴 [API THROTTLED]', response.request().method(), url);
      try {
        const body = await response.text();
        console.error('  Response:', body);
      } catch (e) {
        // Ignore if we can't read the body
      }
    } else if (status >= 400 && status < 500) {
      console.error(`\n🔴 [API CLIENT ERROR ${status}]`, response.request().method(), url);
      try {
        const body = await response.text();
        console.error('  Response:', body);
      } catch (e) {
        // Ignore if we can't read the body
      }
    } else if (status >= 500) {
      console.error(`\n🔴 [API SERVER ERROR ${status}]`, response.request().method(), url);
      try {
        const body = await response.text();
        console.error('  Response:', body);
      } catch (e) {
        // Ignore if we can't read the body
      }
    }
  });

  console.log('✅ Browser logging enabled (console errors, network failures, API errors)');
};
