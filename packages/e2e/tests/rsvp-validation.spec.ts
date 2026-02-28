import { test, expect } from '../src/fixtures';
import type { Page, Route } from '@playwright/test';

/**
 * E2E tests for RSVP form client-side validation.
 *
 * Validation is triggered by dispatching a submit event on the form via
 * page.evaluate(), which fires the Astro inline script's submit handler.
 * Error spans (#error-<field>) are checked for non-empty content.
 */

const API_BASE_URL = 'http://localhost:8000';

// ============================================================================
// Helpers
// ============================================================================

interface GuestInfoOverrides {
  first_name?: string;
  last_name?: string;
  attending?: boolean | null;
  is_plus_one?: boolean;
  plus_one?: Record<string, unknown> | null;
  dietary_requirements?: Array<{ requirement_type: string; notes: string | null }>;
}

async function mockGuestInfo(
  page: Page,
  token: string,
  overrides: GuestInfoOverrides = {}
): Promise<void> {
  await page.route(`${API_BASE_URL}/api/v1/guests/${token}/info`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        guest_uuid: 'test-uuid',
        first_name: '',
        last_name: '',
        phone: null,
        status: 'pending',
        is_plus_one: false,
        is_family_member: false,
        family_id: null,
        family_members: [],
        plus_one: null,
        dietary_requirements: [],
        attending: null,
        allergies: null,
        ...overrides,
      }),
    });
  });
}

async function mockRSVPSubmit(page: Page, token: string): Promise<void> {
  await page.route(`${API_BASE_URL}/api/v1/guests/${token}/rsvp`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        message: 'Thank you for confirming your attendance!',
        attending: true,
        status: 'confirmed',
      }),
    });
  });
}

/** Dispatch submit event on the form via page.evaluate(). */
async function triggerSubmit(page: Page): Promise<void> {
  await page.evaluate(() => {
    const form = document.getElementById('rsvp-form');
    form?.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  });
  // Small wait for synchronous validation + DOM updates to complete
  await page.waitForTimeout(100);
}

// ============================================================================
// Tests
// ============================================================================

test.describe('RSVP Form Validation', () => {
  test('missing first name shows error', async ({ page, language }) => {
    const token = 'test-token-val-firstname';
    await mockGuestInfo(page, token);
    await mockRSVPSubmit(page, token);

    await page.goto(`/${language}/rsvp?token=${token}`);
    await page.waitForLoadState('networkidle');

    // Leave first_name empty, fill last_name
    await page.locator('#last_name').fill('Smit');

    await triggerSubmit(page);

    await expect(page.locator('#error-first_name')).not.toBeEmpty();
  });

  test('missing last name shows error', async ({ page, language }) => {
    const token = 'test-token-val-lastname';
    await mockGuestInfo(page, token);
    await mockRSVPSubmit(page, token);

    await page.goto(`/${language}/rsvp?token=${token}`);
    await page.waitForLoadState('networkidle');

    // Fill first_name, leave last_name empty
    await page.locator('#first_name').fill('Jan');

    await triggerSubmit(page);

    await expect(page.locator('#error-last_name')).not.toBeEmpty();
  });

  test('dietary "other" without notes shows error', async ({ page, language }) => {
    const token = 'test-token-val-dietary';
    await mockGuestInfo(page, token, {
      first_name: 'Jan',
      last_name: 'Smit',
      attending: true,
      dietary_requirements: [{ requirement_type: 'other', notes: null }],
    });
    await mockRSVPSubmit(page, token);

    await page.goto(`/${language}/rsvp?token=${token}`);
    await page.waitForLoadState('networkidle');

    await triggerSubmit(page);

    await expect(page.locator('#error-dietary_notes')).not.toBeEmpty();
  });

  test('dietary "other" with notes has no error', async ({ page, language }) => {
    const token = 'test-token-val-dietary-ok';
    await mockGuestInfo(page, token, {
      first_name: 'Jan',
      last_name: 'Smit',
      attending: true,
      dietary_requirements: [{ requirement_type: 'other', notes: 'No onions' }],
    });
    await mockRSVPSubmit(page, token);

    await page.goto(`/${language}/rsvp?token=${token}`);
    await page.waitForLoadState('networkidle');

    await triggerSubmit(page);

    await expect(page.locator('#error-dietary_notes')).toBeEmpty();
  });

  test('plus-one missing email shows error', async ({ page, language }) => {
    const token = 'test-token-val-po-email';
    await mockGuestInfo(page, token, {
      first_name: 'Jan',
      last_name: 'Smit',
      attending: true,
      plus_one: { email: '', first_name: 'Jane', last_name: 'Doe' },
    });
    await mockRSVPSubmit(page, token);

    await page.goto(`/${language}/rsvp?token=${token}`);
    await page.waitForLoadState('networkidle');

    await triggerSubmit(page);

    await expect(page.locator('#error-plus_one_email')).not.toBeEmpty();
  });

  test('plus-one missing names shows errors', async ({ page, language }) => {
    const token = 'test-token-val-po-names';
    await mockGuestInfo(page, token, {
      first_name: 'Jan',
      last_name: 'Smit',
      attending: true,
      plus_one: { email: 'plusone@example.com', first_name: '', last_name: '' },
    });
    await mockRSVPSubmit(page, token);

    await page.goto(`/${language}/rsvp?token=${token}`);
    await page.waitForLoadState('networkidle');

    await triggerSubmit(page);

    await expect(page.locator('#error-plus_one_first_name')).not.toBeEmpty();
    await expect(page.locator('#error-plus_one_last_name')).not.toBeEmpty();
  });

  test('plus-one dietary "other" without notes shows error', async ({ page, language }) => {
    const token = 'test-token-val-po-dietary';
    await mockGuestInfo(page, token, {
      first_name: 'Jan',
      last_name: 'Smit',
      attending: true,
      plus_one: {
        email: 'plusone@example.com',
        first_name: 'Jane',
        last_name: 'Doe',
        dietary_requirements: [{ requirement_type: 'other', notes: null }],
      },
    });
    await mockRSVPSubmit(page, token);

    await page.goto(`/${language}/rsvp?token=${token}`);
    await page.waitForLoadState('networkidle');

    await triggerSubmit(page);

    await expect(page.locator('#error-plus_one_dietary_notes')).not.toBeEmpty();
  });

  test('not attending with valid names has no field errors', async ({ page, language }) => {
    const token = 'test-token-val-not-attending';
    await mockGuestInfo(page, token, {
      first_name: 'Jan',
      last_name: 'Smit',
      attending: false,
    });
    await mockRSVPSubmit(page, token);

    await page.goto(`/${language}/rsvp?token=${token}`);
    await page.waitForLoadState('networkidle');

    await triggerSubmit(page);

    const errorSpans = page.locator('.field-error');
    const count = await errorSpans.count();
    for (let i = 0; i < count; i++) {
      await expect(errorSpans.nth(i)).toBeEmpty();
    }
  });

  test('errors clear when corrected and resubmitted', async ({ page, language }) => {
    const token = 'test-token-val-clear';
    await mockGuestInfo(page, token);
    await mockRSVPSubmit(page, token);

    await page.goto(`/${language}/rsvp?token=${token}`);
    await page.waitForLoadState('networkidle');

    // First submit: first_name empty → error
    await triggerSubmit(page);
    await expect(page.locator('#error-first_name')).not.toBeEmpty();

    // Fill first_name and resubmit
    await page.locator('#first_name').fill('Jan');
    await triggerSubmit(page);

    // Error for first_name should be gone
    await expect(page.locator('#error-first_name')).toBeEmpty();
  });

  test('Dutch locale shows Dutch error message', async ({ page }) => {
    const token = 'test-token-val-nl';
    await mockGuestInfo(page, token);
    await mockRSVPSubmit(page, token);

    await page.goto(`/nl/rsvp?token=${token}`);
    await page.waitForLoadState('networkidle');

    await triggerSubmit(page);

    await expect(page.locator('#error-first_name')).toHaveText('Voornaam is verplicht');
  });

  test('Spanish locale shows Spanish error message', async ({ page }) => {
    const token = 'test-token-val-es';
    await mockGuestInfo(page, token);
    await mockRSVPSubmit(page, token);

    await page.goto(`/es/rsvp?token=${token}`);
    await page.waitForLoadState('networkidle');

    await triggerSubmit(page);

    await expect(page.locator('#error-first_name')).toHaveText('El nombre es obligatorio');
  });
});
