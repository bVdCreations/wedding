import { test as base } from '@playwright/test';
import type { Page, APIRequestContext } from '@playwright/test';

/**
 * Test configuration options
 */
export interface TestOptions {
  frontendURL: string;
  apiURL: string;
}

/**
 * Custom fixtures for e2e tests
 */
export interface TestFixtures {
  frontendURL: string;
  apiURL: string;
  apiRequest: APIRequestContext;
}

/**
 * Create custom test with fixtures
 */
export const test = base.extend<TestFixtures>({
  frontendURL: async ({}, use) => {
    await use(process.env.FRONTEND_URL || 'http://localhost:4321');
  },
  apiURL: async ({}, use) => {
    await use(process.env.API_URL || 'http://localhost:8000');
  },
  apiRequest: async ({ request }, use) => {
    // Use the request context from the test
    await use(request);
  },
});

/**
 * Re-export expect from Playwright
 */
export { expect } from '@playwright/test';
