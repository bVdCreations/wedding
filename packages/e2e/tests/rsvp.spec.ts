import { test, expect } from '../src/fixtures';

/**
 * E2E tests for the RSVP flow
 *
 * These tests verify the full-stack integration between the frontend
 * and backend API for the wedding RSVP functionality.
 *
 * Tests run against the configured language (default: 'en').
 * Set TEST_LANGUAGE env var to test other languages (en, es, nl).
 */

test.describe('RSVP Page', () => {
  test.beforeEach(async ({ page, language }) => {
    // Navigate to the RSVP page with language prefix and a token
    // (the form is hidden when no token query param is present)
    await page.goto(`/${language}/rsvp?token=test-token`);
  });

  test('should display the RSVP form', async ({ page }) => {
    // Check that the main heading is visible (matches any language)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

    // Check that the form is visible
    await expect(page.locator('#rsvp-form')).toBeVisible();

    // Check that name input fields exist (by id since labels vary by language)
    await expect(page.locator('#first_name')).toBeVisible();
    await expect(page.locator('#last_name')).toBeVisible();
  });

  test('should validate required fields', async ({ page }) => {
    // Try to submit without filling required fields
    await page.locator('button[type="submit"]').click();

    // Check that HTML5 validation prevents submission
    // The form should show validation errors
    const firstNameInput = page.locator('#first_name');
    await expect(firstNameInput).toHaveAttribute('required', '');
  });

  test('should show attending options', async ({ page }) => {
    // Check that attending radio buttons are visible (by value since labels vary)
    await expect(page.locator('input[name="attending"][value="yes"]')).toBeVisible();
    await expect(page.locator('input[name="attending"][value="no"]')).toBeVisible();
  });

  test('should accept valid RSVP submission', async ({ page, apiRequest }) => {
    // Note: This test requires the backend to be running
    // and properly configured to handle form submissions

    // Fill in the form using element ids (language-independent)
    await page.locator('#first_name').fill('John');
    await page.locator('#last_name').fill('Doe');
    await page.locator('#phone').fill('+1234567890');

    // Select attending
    await page.locator('input[name="attending"][value="yes"]').check();

    // Note: Full submission test would require:
    // 1. Creating a valid guest token in the database
    // 2. Using that token in the form submission
    // This is a placeholder for the happy path test
  });

  test('should handle declining RSVP', async ({ page }) => {
    // Fill in the form using element ids (language-independent)
    await page.locator('#first_name').fill('Jane');
    await page.locator('#last_name').fill('Smith');

    // Select not attending
    await page.locator('input[name="attending"][value="no"]').check();

    // The form should still be submittable
    const submitButton = page.locator('button[type="submit"]');
    await expect(submitButton).toBeVisible();
  });
});

test.describe('Home Page', () => {
  test('should redirect root to default language', async ({ page }) => {
    // Navigate to root
    await page.goto('/');

    // Should redirect to /en (default language)
    await expect(page).toHaveURL(/\/en\/?$/);
  });

  test('should display language switcher', async ({ page, language }) => {
    await page.goto(`/${language}`);

    // Check that language switcher is visible with all language options
    await expect(page.locator('.language-switcher')).toBeVisible();
    await expect(page.locator('.language-switcher a[href="/en"]')).toBeVisible();
    await expect(page.locator('.language-switcher a[href="/es"]')).toBeVisible();
    await expect(page.locator('.language-switcher a[href="/nl"]')).toBeVisible();
  });

  test('should navigate between languages', async ({ page }) => {
    // Start at English home page
    await page.goto('/en');
    await expect(page).toHaveURL(/\/en\/?$/);

    // Click Spanish language link
    await page.locator('.language-switcher a[href="/es"]').click();
    await expect(page).toHaveURL(/\/es\/?$/);

    // Click Dutch language link
    await page.locator('.language-switcher a[href="/nl"]').click();
    await expect(page).toHaveURL(/\/nl\/?$/);
  });

  test('should preserve path when switching language', async ({ page }) => {
    // Start at English RSVP page
    await page.goto('/en/rsvp');
    await expect(page).toHaveURL(/\/en\/rsvp/);

    // Click Spanish language link (use prefix match to handle optional trailing slash)
    await page.locator('.language-switcher a[href^="/es/rsvp"]').click();
    await expect(page).toHaveURL(/\/es\/rsvp/);
  });
});

test.describe('RSVP Redirect', () => {
  test('should redirect to request page when no token is present', async ({ page, language }) => {
    // Navigate to RSVP page without a token
    await page.goto(`/${language}/rsvp`);
    
    // Wait for the redirect to complete
    await page.waitForURL(`**/${language}/rsvp/request**`);
    
    // Verify we're on the request page
    await expect(page).toHaveURL(new RegExp(`/${language}/rsvp/request/?$`));
  });

  test('should redirect to request page when token is empty', async ({ page, language }) => {
    // Navigate to RSVP page with empty token
    await page.goto(`/${language}/rsvp?token=`);
    
    // Wait for the redirect to complete
    await page.waitForURL(`**/${language}/rsvp/request**`);
    
    // Verify we're on the request page
    await expect(page).toHaveURL(new RegExp(`/${language}/rsvp/request/?$`));
  });

  test('should not redirect when valid token is present', async ({ page, language }) => {
    // Navigate to RSVP page with a token
    await page.goto(`/${language}/rsvp?token=test-token`);
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Verify we're still on the RSVP page (not redirected)
    await expect(page).toHaveURL(new RegExp(`/${language}/rsvp\\?token=test-token`));
    
    // Verify the form is visible
    await expect(page.locator('#rsvp-form')).toBeVisible();
  });
});

test.describe('API Integration', () => {
  test('should return 404 for non-existent guest', async ({ apiRequest }) => {
    // Test that invalid tokens return 404
    const response = await apiRequest.get('/guests/invalid_token_123');
    expect(response.status()).toBe(404);
  });
});
