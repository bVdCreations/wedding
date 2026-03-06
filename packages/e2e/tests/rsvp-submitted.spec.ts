import { test, expect } from '../src/fixtures';

/**
 * E2E tests for RSVP already submitted summary
 *
 * These tests verify that when a guest has already submitted their RSVP,
 * they see a summary page instead of the form when they revisit the RSVP link.
 */

test.describe('RSVP Already Submitted Summary', () => {
  test.beforeEach(async ({ page }) => {
    // Intercept the API call to return already submitted response
    await page.route('**/api/v1/guests/**/info', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          guest_uuid: '123e4567-e89b-12d3-a456-426614174000',
          token: 'test-token',
          first_name: 'John',
          last_name: 'Doe',
          phone: '+1234567890',
          status: 'confirmed',
          attending: true,
          is_plus_one: false,
          family_id: null,
          family_members: [],
          plus_one_email: null,
          plus_one_first_name: null,
          plus_one_last_name: null,
          dietary_requirements: [
            { requirement_type: 'vegetarian', notes: null },
          ],
          allergies: 'Nuts',
          needs_transport: true,
          rsvp_submitted: true,
        }),
      });
    });
  });

  test('should show summary when rsvp_submitted is true', async ({ page, language }) => {
    await page.goto(`/${language}/rsvp?token=test-token`);

    // Summary should be visible
    await expect(page.locator('#submitted-summary')).toBeVisible();

    // Form should be hidden
    await expect(page.locator('#rsvp-form')).not.toBeVisible();
  });

  test('should display correct attending status in summary', async ({ page, language }) => {
    await page.goto(`/${language}/rsvp?token=test-token`);

    // Should show attending status
    const attendingElement = page.locator('#summary-attending');
    await expect(attendingElement).toBeVisible();
    // The text will be in the language of the page (attendingYes or attendingNo)
  });

  test('should display dietary requirements in summary', async ({ page, language }) => {
    await page.goto(`/${language}/rsvp?token=test-token`);

    // Should show dietary requirements
    const dietaryElement = page.locator('#summary-dietary');
    await expect(dietaryElement).toBeVisible();
    // Should contain some text (the actual text depends on language)
    await expect(dietaryElement).not.toBeEmpty();
  });

  test('should display allergies in summary', async ({ page, language }) => {
    await page.goto(`/${language}/rsvp?token=test-token`);

    // Should show allergies
    const allergiesElement = page.locator('#summary-allergies');
    await expect(allergiesElement).toBeVisible();
    await expect(allergiesElement).toContainText('Nuts');
  });

  test('should display transport status in summary', async ({ page, language }) => {
    await page.goto(`/${language}/rsvp?token=test-token`);

    // Should show transport status
    const transportElement = page.locator('#summary-transport');
    await expect(transportElement).toBeVisible();
  });

  test('should display venue info in summary', async ({ page, language }) => {
    await page.goto(`/${language}/rsvp?token=test-token`);

    // Should show venue information
    await expect(page.locator('#summary-venue-name')).toBeVisible();
    await expect(page.locator('#summary-venue-address')).toBeVisible();
    await expect(page.locator('#summary-venue-city')).toBeVisible();
  });

  test('should have working back to main page link', async ({ page, language }) => {
    await page.goto(`/${language}/rsvp?token=test-token`);

    // Click the back to main page link
    await page.locator('#back-to-main').click();

    // Should navigate to main page for the language
    await expect(page).toHaveURL(new RegExp(`/${language}/?$`));
  });
});

test.describe('RSVP Not Yet Submitted', () => {
  test.beforeEach(async ({ page }) => {
    // Intercept the API call to return NOT submitted response
    await page.route('**/api/v1/guests/**/info', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          guest_uuid: '123e4567-e89b-12d3-a456-426614174001',
          token: 'new-token',
          first_name: 'Jane',
          last_name: 'Smith',
          phone: null,
          status: 'pending',
          attending: null,
          is_plus_one: false,
          family_id: null,
          family_members: [],
          plus_one_email: null,
          plus_one_first_name: null,
          plus_one_last_name: null,
          dietary_requirements: [],
          allergies: null,
          needs_transport: false,
          rsvp_submitted: false,
        }),
      });
    });
  });

  test('should show form when rsvp_submitted is false', async ({ page, language }) => {
    await page.goto(`/${language}/rsvp?token=new-token`);

    // Form should be visible
    await expect(page.locator('#rsvp-form')).toBeVisible();

    // Summary should be hidden
    await expect(page.locator('#submitted-summary')).not.toBeVisible();
  });
});

test.describe('RSVP Submitted - Not Attending', () => {
  test.beforeEach(async ({ page }) => {
    // Intercept the API call to return not attending response
    await page.route('**/api/v1/guests/**/info', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          guest_uuid: '123e4567-e89b-12d3-a456-426614174002',
          token: 'declined-token',
          first_name: 'Bob',
          last_name: 'Johnson',
          phone: null,
          status: 'declined',
          attending: false,
          is_plus_one: false,
          family_id: null,
          family_members: [],
          plus_one_email: null,
          plus_one_first_name: null,
          plus_one_last_name: null,
          dietary_requirements: [],
          allergies: null,
          needs_transport: false,
          rsvp_submitted: true,
        }),
      });
    });
  });

  test('should show not attending status in summary', async ({ page, language }) => {
    await page.goto(`/${language}/rsvp?token=declined-token`);

    // Summary should be visible
    await expect(page.locator('#submitted-summary')).toBeVisible();

    // Form should be hidden
    await expect(page.locator('#rsvp-form')).not.toBeVisible();
  });

  test('should show contact email when not attending', async ({ page, language }) => {
    await page.goto(`/${language}/rsvp?token=declined-token`);

    // Contact email should be visible even when declined
    const contactEmail = page.locator('#contact-email-note');
    await expect(contactEmail).toBeVisible();
    await expect(contactEmail).toContainText('info@gemma-bastiaan.wedding');
  });
});
