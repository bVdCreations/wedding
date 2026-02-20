import { test as base } from '@playwright/test';
import type { Page, APIRequestContext } from '@playwright/test';

/**
 * Supported languages for i18n
 */
export type Language = 'en' | 'es' | 'nl';

/**
 * Test configuration options
 */
export interface TestOptions {
  frontendURL: string;
  apiURL: string;
  language: Language;
}

/**
 * Custom fixtures for e2e tests
 */
export interface TestFixtures {
  frontendURL: string;
  apiURL: string;
  language: Language;
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
  language: async ({}, use) => {
    await use((process.env.TEST_LANGUAGE as Language) || 'en');
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
