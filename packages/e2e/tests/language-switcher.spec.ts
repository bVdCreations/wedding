import { test, expect } from '../src/fixtures';

const API_BASE_URL = 'http://localhost:8000';
const token = 'abc123';

// Mock the guest info endpoint so the RSVP page renders the form, not an error.
async function mockGuestInfo(page: Parameters<typeof test>[1]['page'], token: string) {
  await page.route(`${API_BASE_URL}/api/v1/guests/${token}/info`, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        guest_uuid: token,
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
    })
  );
}

test.describe('Language switcher — query parameter preservation', () => {
  test('switcher links on RSVP page include the token', async ({ page }) => {
    await mockGuestInfo(page, token);
    await page.goto(`/en/rsvp?token=${token}`);
    await page.waitForLoadState('networkidle');

    const esLink = page.locator('.language-switcher a', { hasText: 'es' });
    const nlLink = page.locator('.language-switcher a', { hasText: 'nl' });

    await expect(esLink).toHaveAttribute('href', `/es/rsvp?token=${token}`);
    await expect(nlLink).toHaveAttribute('href', `/nl/rsvp?token=${token}`);
  });

  test('switcher links on RSVP page include the token that end with a slash', async ({ page }) => {
    await mockGuestInfo(page, token);
    await page.goto(`/en/rsvp/?token=${token}`);
    await page.waitForLoadState('networkidle');

    const esLink = page.locator('.language-switcher a', { hasText: 'es' });
    const nlLink = page.locator('.language-switcher a', { hasText: 'nl' });

    await expect(esLink).toHaveAttribute('href', `/es/rsvp/?token=${token}`);
    await expect(nlLink).toHaveAttribute('href', `/nl/rsvp/?token=${token}`);
  });

  test('clicking a switcher link keeps the token in the URL', async ({ page }) => {
    await mockGuestInfo(page, token);
    await page.goto(`/en/rsvp?token=${token}`);
    await page.waitForLoadState('networkidle');

    await page.locator('.language-switcher a', { hasText: 'es' }).click();
    await page.waitForLoadState('networkidle');

    expect(page.url()).toContain(`token=${token}`);
    expect(page.url()).toContain('/es/rsvp');
  });

  test('switching back to the original language keeps the token', async ({ page }) => {
    await mockGuestInfo(page, token);
    await page.goto(`/es/rsvp?token=${token}`);
    await page.waitForLoadState('networkidle');

    await page.locator('.language-switcher a', { hasText: 'en' }).click();
    await page.waitForLoadState('networkidle');

    expect(page.url()).toContain(`token=${token}`);
    expect(page.url()).toContain('/en/rsvp');
  });

  test('RSVP form is visible after switching language with token', async ({ page }) => {
    await mockGuestInfo(page, token);
    await page.goto(`/en/rsvp?token=${token}`);
    await page.waitForLoadState('networkidle');

    await page.locator('.language-switcher a', { hasText: 'nl' }).click();
    await page.waitForLoadState('networkidle');

    await expect(page.locator('#rsvp-form')).toBeVisible();
  });
});

test.describe('Language switcher — pages without query params', () => {
  test('switcher links on home page have no query string', async ({ page }) => {
    await page.goto('/en');

    const esLink = page.locator('.language-switcher a', { hasText: 'es' });
    const nlLink = page.locator('.language-switcher a', { hasText: 'nl' });

    await expect(esLink).toHaveAttribute('href', '/es');
    await expect(nlLink).toHaveAttribute('href', '/nl');
  });

  test('current language link on RSVP page preserves token', async ({ page }) => {
    await mockGuestInfo(page, token);
    await page.goto(`/en/rsvp?token=${token}`);
    await page.waitForLoadState('networkidle');

    // The active language link should also point to the correct URL with token.
    const enLink = page.locator('.language-switcher a', { hasText: 'en' });
    await expect(enLink).toHaveAttribute('href', `/en/rsvp?token=${token}`);
  });
});
