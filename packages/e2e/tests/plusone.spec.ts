import { test, expect } from '../src/fixtures';
import type { Page, Route } from '@playwright/test';

/**
 * E2E tests for plus-one functionality with mocked backend.
 *
 * These tests use Playwright's route interception to mock API responses,
 * allowing frontend testing without a running backend.
 */

const API_BASE_URL = 'http://localhost:8000';

interface GuestInfo {
  guest_uuid: string;
  first_name: string;
  last_name: string;
  phone: string | null;
  status: string;
  is_plus_one: boolean;
  is_family_member: boolean;
  family_id: string | null;
  family_members: unknown[];
  plus_one: PlusOneInfo | null;
  dietary_requirements: unknown[];
  attending: boolean | null;
  allergies: string | null;
  needs_transport: boolean;
  rsvp_submitted: boolean;
}

interface PlusOneInfo {
  email: string;
  first_name: string;
  last_name: string;
  allergies: string | null;
  dietary_requirements: Array<{ requirement_type: string; notes: string | null }>;
}

function createMockGuestInfo(overrides: Partial<GuestInfo> = {}): GuestInfo {
  return {
    guest_uuid: 'test-uuid',
    first_name: 'John',
    last_name: 'Doe',
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
    needs_transport: false,
    rsvp_submitted: false,
    ...overrides,
  };
}

async function mockGuestInfoEndpoint(
  page: Page,
  token: string,
  guestInfo: GuestInfo = createMockGuestInfo()
): Promise<void> {
  await page.route(`${API_BASE_URL}/api/v1/guests/${token}/info`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(guestInfo),
    });
  });
}

async function mockRSVPSubmitEndpoint(
  page: Page,
  token: string,
  response: { message: string; attending: boolean; status: string }
): Promise<void> {
  await page.route(`${API_BASE_URL}/api/v1/guests/${token}/rsvp`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(response),
    });
  });
}

async function submitRSVPForm(
  page: Page,
  token: string,
  data: {
    attending: boolean;
    firstName: string;
    lastName: string;
    phone?: string;
    allergies?: string;
    dietaryRequirements?: string[];
    dietaryNotes?: string;
    plusOneDetails?: {
      email: string;
      first_name: string;
      last_name: string;
      allergies?: string;
      dietary_requirements?: Array<{ requirement_type: string; notes: string | null }>;
    };
  }
): Promise<{ success: boolean; data: Record<string, unknown> }> {
  return page.evaluate(
    async ({ apiHost, token, data }) => {
      const dietaryReqs = (data.dietaryRequirements || []).map((req) => ({
        requirement_type: req,
        notes: req === 'other' ? data.dietaryNotes || null : null,
      }));

      let plusOneDetailsWithDietary = null;
      if (data.plusOneDetails) {
        plusOneDetailsWithDietary = {
          ...data.plusOneDetails,
          dietary_requirements: data.plusOneDetails.dietary_requirements || [],
        };
      }

      const response = await fetch(`${apiHost}/api/v1/guests/${token}/rsvp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          attending: data.attending,
          guest_info: {
            first_name: data.firstName,
            last_name: data.lastName,
            phone: data.phone || null,
          },
          dietary_requirements: dietaryReqs,
          allergies: data.allergies || null,
          plus_one_details: plusOneDetailsWithDietary,
          family_member_updates: {},
        }),
      });
      const responseData = await response.json();
      return { success: response.ok, data: responseData };
    },
    { apiHost: API_BASE_URL, token, data }
  );
}

test.describe('Plus-One Prefill Display', () => {
  const testToken = 'test-token-plus-one';

  test('should display plus-one name and email in prefill', async ({ page, language }) => {
    await mockGuestInfoEndpoint(
      page,
      testToken,
      createMockGuestInfo({
        attending: true,
        plus_one: {
          email: 'jane@example.com',
          first_name: 'Jane',
          last_name: 'Smith',
          allergies: null,
          dietary_requirements: [],
        },
      })
    );

    await page.goto(`/${language}/rsvp?token=${testToken}`);
    await page.waitForLoadState('networkidle');

    await expect(page.locator('#plus-one-details-section')).not.toHaveAttribute(
      'style',
      /display:\s*none/
    );
  });

  test('should display plus-one allergies when prefill has allergies', async ({ page, language }) => {
    await mockGuestInfoEndpoint(
      page,
      testToken,
      createMockGuestInfo({
        attending: true,
        plus_one: {
          email: 'jane@example.com',
          first_name: 'Jane',
          last_name: 'Smith',
          allergies: 'Peanut allergy',
          dietary_requirements: [],
        },
      })
    );

    await page.goto(`/${language}/rsvp?token=${testToken}`);
    await page.waitForLoadState('networkidle');

    await expect(page.locator('#plus-one-details-section')).not.toHaveAttribute(
      'style',
      /display:\s*none/
    );

    await expect(page.locator('#plus-one-allergies-section')).not.toHaveAttribute(
      'style',
      /display:\s*none/
    );
    await expect(page.locator('#plus_one_allergies')).toHaveValue('Peanut allergy');
  });

  test('should display plus-one dietary requirements when prefill has dietary', async ({
    page,
    language,
  }) => {
    await mockGuestInfoEndpoint(
      page,
      testToken,
      createMockGuestInfo({
        attending: true,
        plus_one: {
          email: 'jane@example.com',
          first_name: 'Jane',
          last_name: 'Smith',
          allergies: null,
          dietary_requirements: [{ requirement_type: 'vegetarian', notes: null }],
        },
      })
    );

    await page.goto(`/${language}/rsvp?token=${testToken}`);
    await page.waitForLoadState('networkidle');

    await expect(page.locator('#plus-one-dietary-vegetarian')).toBeChecked();
  });

  test('should display plus-one dietary notes when "other" dietary is prefilled', async ({
    page,
    language,
  }) => {
    await mockGuestInfoEndpoint(
      page,
      testToken,
      createMockGuestInfo({
        attending: true,
        plus_one: {
          email: 'jane@example.com',
          first_name: 'Jane',
          last_name: 'Smith',
          allergies: null,
          dietary_requirements: [{ requirement_type: 'other', notes: 'No spicy food' }],
        },
      })
    );

    await page.goto(`/${language}/rsvp?token=${testToken}`);
    await page.waitForLoadState('networkidle');

    await expect(page.locator('#plus-one-dietary-other')).toBeChecked();
    await expect(page.locator('#plus-one-dietary-notes-section')).not.toHaveAttribute(
      'style',
      /display:\s*none/
    );
    await expect(page.locator('#plus_one_dietary_notes')).toHaveValue('No spicy food');
  });

  test('should submit RSVP with plus-one allergies', async ({ page, language }) => {
    let capturedRequest: Record<string, unknown> | null = null;

    await mockGuestInfoEndpoint(
      page,
      testToken,
      createMockGuestInfo({
        attending: true,
        plus_one: {
          email: 'jane@example.com',
          first_name: 'Jane',
          last_name: 'Smith',
          allergies: null,
          dietary_requirements: [],
        },
      })
    );
    await page.route(`${API_BASE_URL}/api/v1/guests/${testToken}/rsvp`, async (route: Route) => {
      capturedRequest = JSON.parse(route.request().postData() || '{}');
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Thank you for confirming!',
          attending: true,
          status: 'confirmed',
        }),
      });
    });

    await page.goto(`/${language}/rsvp?token=${testToken}`);
    await page.waitForLoadState('networkidle');

    const result = await submitRSVPForm(page, testToken, {
      attending: true,
      firstName: 'John',
      lastName: 'Doe',
      plusOneDetails: {
        email: 'jane@example.com',
        first_name: 'Jane',
        last_name: 'Smith',
        allergies: 'Tree nut allergy',
      },
    });

    expect(result.success).toBe(true);
    expect(capturedRequest).not.toBeNull();
    const plusOneDetails = capturedRequest!.plus_one_details as {
      allergies: string;
      dietary_requirements: unknown[];
    };
    expect(plusOneDetails.allergies).toBe('Tree nut allergy');
    expect(plusOneDetails.dietary_requirements).toEqual([]);
  });

  test('should prefill plus-one first name and last name', async ({ page, language }) => {
    await mockGuestInfoEndpoint(
      page,
      testToken,
      createMockGuestInfo({
        attending: true,
        plus_one: {
          email: 'jane@example.com',
          first_name: 'Jane',
          last_name: 'Smith',
          allergies: null,
          dietary_requirements: [],
        },
      })
    );

    await page.goto(`/${language}/rsvp?token=${testToken}`);
    await page.waitForLoadState('networkidle');

    const firstNameInput = page.locator('#plus_one_first_name');
    await expect(firstNameInput).toBeVisible();
    await expect(firstNameInput).toHaveValue('Jane');

    const lastNameInput = page.locator('#plus_one_last_name');
    await expect(lastNameInput).toBeVisible();
    await expect(lastNameInput).toHaveValue('Smith');
  });

  test('should prefill plus-one allergies', async ({ page, language }) => {
    await mockGuestInfoEndpoint(
      page,
      testToken,
      createMockGuestInfo({
        attending: true,
        plus_one: {
          email: 'jane@example.com',
          first_name: 'Jane',
          last_name: 'Smith',
          allergies: 'Peanut allergy',
          dietary_requirements: [],
        },
      })
    );

    await page.goto(`/${language}/rsvp?token=${testToken}`);
    await page.waitForLoadState('networkidle');

    const allergiesInput = page.locator('#plus_one_allergies');
    await expect(allergiesInput).toBeVisible();
    await expect(allergiesInput).toHaveValue('Peanut allergy');
  });

  test('should show contact email in form when plus-one is allowed', async ({ page, language }) => {
    await mockGuestInfoEndpoint(
      page,
      testToken,
      createMockGuestInfo({
        attending: null,
        plus_one: {
          email: 'jane@example.com',
          first_name: 'Jane',
          last_name: 'Smith',
          allergies: null,
          dietary_requirements: [],
        },
      })
    );

    await page.goto(`/${language}/rsvp?token=${testToken}`);
    await page.waitForLoadState('networkidle');

    // Contact email should be visible in the form
    const contactEmail = page.locator('#contact-email-note-form');
    await expect(contactEmail).toBeVisible();
    await expect(contactEmail).toContainText('info@gemma-bastiaan.wedding');
  });
});
