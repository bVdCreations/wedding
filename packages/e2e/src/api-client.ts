import { APIRequestContext } from '@playwright/test';

export interface GuestData {
  name: string;
  email: string;
  phone?: string;
  has_plus_one: boolean;
  plus_one_name?: string;
}

export interface RSVPData {
  attending: boolean;
  dietary_restrictions?: string[];
  plus_one_attending?: boolean;
  plus_one_dietary_restrictions?: string[];
}

/**
 * API client for backend interactions during e2e tests
 */
export class ApiClient {
  constructor(
    private request: APIRequestContext,
    private baseURL: string
  ) {}

  /**
   * Health check endpoint
   */
  async healthCheck(): Promise<boolean> {
    const response = await this.request.get('/healthz');
    return response.ok();
  }

  /**
   * Get guest info by token
   */
  async getGuestInfo(token: string): Promise<GuestInfoResponse | null> {
    const response = await this.request.get(`/guests/${token}`);
    if (!response.ok()) {
      return null;
    }
    return response.json() as Promise<GuestInfoResponse>;
  }

  /**
   * Update RSVP for a guest
   */
  async updateRSVP(token: string, rsvpData: RSVPData): Promise<boolean> {
    const response = await this.request.patch(`/guests/${token}/rsvp`, {
      data: rsvpData,
    });
    return response.ok();
  }

  /**
   * Create a new guest (for test setup)
   */
  async createGuest(guestData: GuestData): Promise<CreateGuestResponse | null> {
    const response = await this.request.post('/guests', {
      data: guestData,
    });
    if (!response.ok()) {
      return null;
    }
    return response.json() as Promise<CreateGuestResponse>;
  }
}

export interface GuestInfoResponse {
  id: string;
  name: string;
  email: string;
  has_plus_one: boolean;
  plus_one_name?: string;
  rsvp?: {
    attending: boolean;
    dietary_restrictions: string[];
  };
}

export interface CreateGuestResponse {
  id: string;
  token: string;
  name: string;
}
