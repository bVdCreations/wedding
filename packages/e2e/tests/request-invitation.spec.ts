import { test, expect } from '../src/fixtures';
import type { Page, Route } from '@playwright/test';

/**
 * E2E tests for Request Invitation flow.
 *
 * Tests the self-service invitation request page where users can enter
 * their email, first name, and last name to receive an RSVP invitation link.
 */

const API_BASE_URL = 'http://localhost:8000';

// ============================================================================
// Helpers
// ============================================================================

async function mockRequestInvitationSuccess(page: Page): Promise<void> {
  await page.route(`${API_BASE_URL}/api/v1/guests/request-invitation`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        message: 'Check your email for your invitation link',
      }),
    });
  });
}

async function mockRequestInvitationError(page: Page): Promise<void> {
  await page.route(`${API_BASE_URL}/api/v1/guests/request-invitation`, async (route: Route) => {
    await route.fulfill({
      status: 400,
      contentType: 'application/json',
      body: JSON.stringify({
        detail: 'Something went wrong',
      }),
    });
  });
}

async function mockRequestInvitationValidationError(page: Page): Promise<void> {
  await page.route(`${API_BASE_URL}/api/v1/guests/request-invitation`, async (route: Route) => {
    await route.fulfill({
      status: 422,
      contentType: 'application/json',
      body: JSON.stringify({
        detail: 'Validation error',
      }),
    });
  });
}

// ============================================================================
// Tests
// ============================================================================

test.describe('Request Invitation Flow', () => {
  test('can submit valid invitation request', async ({ page, language }) => {
    await mockRequestInvitationSuccess(page);

    await page.goto(`/${language}/rsvp/request`);
    await page.waitForLoadState('networkidle');

    // Fill in the form
    await page.locator('#first_name').fill('John');
    await page.locator('#last_name').fill('Doe');
    await page.locator('#email').fill('john.doe@example.com');

    // Submit the form
    await page.locator('button[type="submit"]').click();

    // Wait for success message
    await expect(page.locator('#success-message')).toBeVisible();
    await expect(page.locator('#success-text')).toContainText('Check your email for your invitation link');

    // Form should be hidden
    await expect(page.locator('#request-form')).not.toBeVisible();
  });

  test('cannot submit with empty fields', async ({ page, language }) => {
    await mockRequestInvitationSuccess(page);

    await page.goto(`/${language}/rsvp/request`);
    await page.waitForLoadState('networkidle');

    // Submit button should be disabled initially
    await expect(page.locator('button[type="submit"]')).toBeDisabled();

    // Fill only email
    await page.locator('#email').fill('john.doe@example.com');

    // Should still be disabled
    await expect(page.locator('button[type="submit"]')).toBeDisabled();

    // Fill first name
    await page.locator('#first_name').fill('John');

    // Should still be disabled
    await expect(page.locator('button[type="submit"]')).toBeDisabled();

    // Fill last name
    await page.locator('#last_name').fill('Doe');

    // Should now be enabled
    await expect(page.locator('button[type="submit"]')).toBeEnabled();
  });

  test('shows error on API failure', async ({ page, language }) => {
    await mockRequestInvitationError(page);

    await page.goto(`/${language}/rsvp/request`);
    await page.waitForLoadState('networkidle');

    // Fill in the form
    await page.locator('#first_name').fill('John');
    await page.locator('#last_name').fill('Doe');
    await page.locator('#email').fill('john.doe@example.com');

    // Submit the form
    await page.locator('button[type="submit"]').click();

    // Wait for error message
    await expect(page.locator('#error-message')).toBeVisible();
    await expect(page.locator('#error-text')).toContainText('went wrong');
  });

  test('shows error on validation failure', async ({ page, language }) => {
    await mockRequestInvitationValidationError(page);

    await page.goto(`/${language}/rsvp/request`);
    await page.waitForLoadState('networkidle');

    // Fill in the form
    await page.locator('#first_name').fill('John');
    await page.locator('#last_name').fill('Doe');
    await page.locator('#email').fill('john.doe@example.com');

    // Submit the form
    await page.locator('button[type="submit"]').click();

    // Wait for error message
    await expect(page.locator('#error-message')).toBeVisible();
  });

  test('validates email format', async ({ page, language }) => {
    await mockRequestInvitationSuccess(page);

    await page.goto(`/${language}/rsvp/request`);
    await page.waitForLoadState('networkidle');

    // Fill in invalid email
    await page.locator('#first_name').fill('John');
    await page.locator('#last_name').fill('Doe');
    await page.locator('#email').fill('not-an-email');

    // Submit button should be disabled
    await expect(page.locator('button[type="submit"]')).toBeDisabled();

    // Fix email
    await page.locator('#email').fill('valid@email.com');

    // Should now be enabled
    await expect(page.locator('button[type="submit"]')).toBeEnabled();
  });

  test('redirects from RSVP page when no token', async ({ page, language }) => {
    await page.goto(`/${language}/rsvp`);
    await page.waitForLoadState('networkidle');

    // Should redirect to request page
    await expect(page).toHaveURL(new RegExp(`/${language}/rsvp/request`));
  });

  test('RSVP page still works with valid token', async ({ page, language }) => {
    const token = 'test-token-123';

    // Mock guest info endpoint
    await page.route(`${API_BASE_URL}/api/v1/guests/${token}/info`, async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          guest_uuid: 'test-uuid',
          first_name: 'Test',
          last_name: 'Guest',
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
        }),
      });
    });

    await page.goto(`/${language}/rsvp?token=${token}`);
    await page.waitForLoadState('networkidle');

    // Should stay on RSVP page and show form
    await expect(page).toHaveURL(new RegExp(`/${language}/rsvp\\?token=${token}`));
    await expect(page.locator('#rsvp-form')).toBeVisible();
  });

  test('Dutch locale shows Dutch text', async ({ page }) => {
    await mockRequestInvitationSuccess(page);

    await page.goto('/nl/rsvp/request');
    await page.waitForLoadState('networkidle');

    // Check for Dutch heading
    await expect(page.locator('h1')).toContainText('Vraag Je Uitnodiging Aan');
  });

  test('Spanish locale shows Spanish text', async ({ page }) => {
    await mockRequestInvitationSuccess(page);

    await page.goto('/es/rsvp/request');
    await page.waitForLoadState('networkidle');

    // Check for Spanish heading
    await expect(page.locator('h1')).toContainText('Solicita Tu Invitación');
  });

  test('English locale shows English text', async ({ page }) => {
    await mockRequestInvitationSuccess(page);

    await page.goto('/en/rsvp/request');
    await page.waitForLoadState('networkidle');

    // Check for English heading
    await expect(page.locator('h1')).toContainText('Request Your Invitation');
  });
});
