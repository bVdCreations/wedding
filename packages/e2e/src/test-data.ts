import type { GuestData, RSVPData } from './api-client';

/**
 * Test data factories for creating consistent test data
 */

/**
 * Generate a random unique token for testing
 */
export function generateTestToken(): string {
  return `test_${Math.random().toString(36).substring(2, 15)}`;
}

/**
 * Create a valid guest data object for tests
 */
export function createTestGuest(overrides?: Partial<GuestData>): GuestData {
  const uniqueId = Math.random().toString(36).substring(2, 8);
  return {
    name: `Test Guest ${uniqueId}`,
    email: `test_${uniqueId}@example.com`,
    phone: '+1234567890',
    has_plus_one: false,
    ...overrides,
  };
}

/**
 * Create a guest with plus one
 */
export function createTestGuestWithPlusOne(overrides?: Partial<GuestData>): GuestData {
  const uniqueId = Math.random().toString(36).substring(2, 8);
  return {
    name: `Test Guest ${uniqueId}`,
    email: `test_${uniqueId}@example.com`,
    phone: '+1234567890',
    has_plus_one: true,
    plus_one_name: `Plus One ${uniqueId}`,
    ...overrides,
  };
}

/**
 * Create valid RSVP data for tests
 */
export function createTestRSVP(overrides?: Partial<RSVPData>): RSVPData {
  return {
    attending: true,
    dietary_restrictions: [],
    plus_one_attending: false,
    ...overrides,
  };
}

/**
 * Declining RSVP data
 */
export function createDecliningRSVP(overrides?: Partial<RSVPData>): RSVPData {
  return {
    attending: false,
    dietary_restrictions: [],
    plus_one_attending: false,
    ...overrides,
  };
}

/**
 * Common dietary restrictions for testing
 */
export const dietaryOptions = [
  'vegetarian',
  'other',
] as const;

/**
 * Get a subset of dietary restrictions for testing
 */
export function getRandomDietaryRestrictions(count: number = 1): string[] {
  const shuffled = [...dietaryOptions].sort(() => 0.5 - Math.random());
  return shuffled.slice(0, count);
}
