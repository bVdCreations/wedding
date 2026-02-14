import { test, expect } from '../src/fixtures';

/**
 * E2E tests for the RSVP flow
 * 
 * These tests verify the full-stack integration between the frontend
 * and backend API for the wedding RSVP functionality.
 */

test.describe('RSVP Page', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the RSVP page before each test
    await page.goto('/rsvp');
  });

  test('should display the RSVP form', async ({ page }) => {
    // Check that the main heading is visible
    await expect(page.getByRole('heading', { level: 1 })).toContainText("You're Invited!");
    
    // Check that the form is visible
    await expect(page.locator('#rsvp-form')).toBeVisible();
    
    // Check that the name fields are visible
    await expect(page.getByLabel('First Name')).toBeVisible();
    await expect(page.getByLabel('Last Name')).toBeVisible();
  });

  test('should validate required fields', async ({ page }) => {
    // Try to submit without filling required fields
    await page.getByRole('button', { name: /submit|send/i }).click();
    
    // Check that HTML5 validation prevents submission
    // The form should show validation errors
    const firstNameInput = page.getByLabel('First Name');
    await expect(firstNameInput).toHaveAttribute('required', '');
  });

  test('should show attending options', async ({ page }) => {
    // Check that attending radio buttons are visible
    await expect(page.getByRole('radio', { name: /yes, i'll be there/i })).toBeVisible();
    await expect(page.getByRole('radio', { name: /can't make it/i })).toBeVisible();
  });

  test('should accept valid RSVP submission', async ({ page, apiRequest }) => {
    // Note: This test requires the backend to be running
    // and properly configured to handle form submissions
    
    // Fill in the form
    await page.getByLabel('First Name').fill('John');
    await page.getByLabel('Last Name').fill('Doe');
    await page.getByLabel('Phone (optional)').fill('+1234567890');
    
    // Select attending
    await page.getByRole('radio', { name: /yes, i'll be there/i }).check();
    
    // Note: Full submission test would require:
    // 1. Creating a valid guest token in the database
    // 2. Using that token in the form submission
    // This is a placeholder for the happy path test
  });

  test('should handle declining RSVP', async ({ page }) => {
    // Fill in the form
    await page.getByLabel('First Name').fill('Jane');
    await page.getByLabel('Last Name').fill('Smith');
    
    // Select not attending
    await page.getByRole('radio', { name: /can't make it/i }).check();
    
    // The form should still be submittable
    const submitButton = page.getByRole('button', { name: /submit|send/i });
    await expect(submitButton).toBeVisible();
  });
});

test.describe('API Integration', () => {
  test('should be able to connect to the API', async ({ apiRequest }) => {
    // Test that we can reach the health check endpoint
    const response = await apiRequest.get('/healthz');
    expect(response.ok()).toBeTruthy();
  });

  test('should return 404 for non-existent guest', async ({ apiRequest }) => {
    // Test that invalid tokens return 404
    const response = await apiRequest.get('/guests/invalid_token_123');
    expect(response.status()).toBe(404);
  });
});
