# RSVP Validation Plan

## Overview

Add client-side (frontend) and server-side (backend) validation to the RSVP form, enforcing the following rules:

### Validation Rules

| Condition | Required Fields |
|-----------|----------------|
| Always | `first_name`, `last_name`, `attending` |
| `attending = yes` + `dietary` includes `other` | `dietary_notes` must not be empty |
| `attending = yes` + `plus_one` is checked | `plus_one_email`, `plus_one_first_name`, `plus_one_last_name` |
| `attending = no` | No additional validation |

---

## 1. Frontend Validation

**File:** `frontend/src/pages/[lang]/rsvp/index.astro`

### Approach

Add a JavaScript validation function that runs on form `submit` before sending the request. Display inline error messages next to the relevant fields. No new dependencies needed — plain JS + CSS.

### Steps

#### 1.1 Add error message elements

For each validated field, add a sibling `<span>` element to display the error:

```html
<input id="first_name" name="first_name" type="text" ... />
<span id="error-first_name" class="field-error" aria-live="polite"></span>
```

Fields needing error spans:
- `first_name`
- `last_name`
- `attending` (radio group — place span after the group)
- `dietary_notes` (only shown when "other" is selected)
- `plus_one_email`
- `plus_one_first_name`
- `plus_one_last_name`

#### 1.2 Add CSS for error styling

```css
.field-error {
  color: #c0392b;
  font-size: 0.85rem;
  display: block;
  margin-top: 0.25rem;
}
input.invalid, textarea.invalid {
  border-color: #c0392b;
}
```

#### 1.3 Add validation logic

Add a `validateForm()` function in the existing `<script>` block:

```js
function validateForm(formData) {
  const errors = {};

  // Always required
  if (!formData.get('first_name')?.trim()) {
    errors['first_name'] = 'First name is required';
  }
  if (!formData.get('last_name')?.trim()) {
    errors['last_name'] = 'Last name is required';
  }

  const attending = formData.get('attending');
  if (!attending) {
    errors['attending'] = 'Please indicate if you will attend';
  }

  if (attending === 'yes') {
    // Dietary "other" requires notes
    const dietary = formData.getAll('dietary');
    if (dietary.includes('other') && !formData.get('dietary_notes')?.trim()) {
      errors['dietary_notes'] = 'Please describe your dietary requirements';
    }

    // Plus one requires name + email
    const hasPlusOne = formData.get('plus_one') === 'on';
    if (hasPlusOne) {
      if (!formData.get('plus_one_email')?.trim()) {
        errors['plus_one_email'] = 'Email is required for your plus one';
      }
      if (!formData.get('plus_one_first_name')?.trim()) {
        errors['plus_one_first_name'] = 'First name is required for your plus one';
      }
      if (!formData.get('plus_one_last_name')?.trim()) {
        errors['plus_one_last_name'] = 'Last name is required for your plus one';
      }
    }
  }

  return errors;
}
```

#### 1.4 Wire validation into submit handler

In the existing form submit handler, call `validateForm()` before building the request payload:

```js
formElement.addEventListener('submit', async (e) => {
  e.preventDefault();
  clearErrors();

  const formData = new FormData(formElement);
  const errors = validateForm(formData);

  if (Object.keys(errors).length > 0) {
    displayErrors(errors);
    // Scroll to first error
    document.querySelector('.field-error:not(:empty)')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    return;
  }

  // ... existing submit logic
});

function clearErrors() {
  document.querySelectorAll('.field-error').forEach(el => el.textContent = '');
  document.querySelectorAll('.invalid').forEach(el => el.classList.remove('invalid'));
}

function displayErrors(errors) {
  for (const [field, message] of Object.entries(errors)) {
    const span = document.getElementById(`error-${field}`);
    if (span) span.textContent = message;
    const input = document.getElementById(field) ?? document.querySelector(`[name="${field}"]`);
    if (input) input.classList.add('invalid');
  }
}
```

---

## 2. Backend Validation

**File:** `src/guests/features/update_rsvp/router.py`

### Approach

Use Pydantic [model validators](https://docs.pydantic.dev/latest/concepts/validators/#model-validators) (`@model_validator`) on the existing request schemas. This keeps validation co-located with the schema definitions and produces clear 422 error responses automatically.

### Steps

#### 2.1 Validate `GuestInfoSubmit` — non-empty name fields

The fields are already typed as `str`, but Pydantic allows empty strings. Add a field validator:

```python
from pydantic import field_validator

class GuestInfoSubmit(BaseModel):
    first_name: str
    last_name: str
    ...

    @field_validator('first_name', 'last_name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('must not be empty')
        return v.strip()
```

#### 2.2 Validate `DietaryRequirement` — notes required when type is `other`

```python
from pydantic import model_validator

class DietaryRequirement(BaseModel):
    requirement_type: DietaryType
    notes: str | None = None

    @model_validator(mode='after')
    def notes_required_for_other(self) -> 'DietaryRequirement':
        if self.requirement_type == DietaryType.OTHER and not (self.notes or '').strip():
            raise ValueError('notes are required when dietary type is "other"')
        return self
```

#### 2.3 Validate `RSVPResponseSubmit` — strip plus_one when not attending

When `attending = False`, ignore/clear any plus_one_details to avoid inconsistent state:

```python
from pydantic import model_validator

class RSVPResponseSubmit(BaseModel):
    attending: bool
    plus_one_details: PlusOneSubmit | None = None
    guest_info: GuestInfoSubmit | None = None
    family_member_updates: dict[str, FamilyMemberSubmit] = []

    @model_validator(mode='after')
    def validate_attendance_requirements(self) -> 'RSVPResponseSubmit':
        if not self.attending:
            # Not attending: clear plus_one (no validation needed)
            self.plus_one_details = None
        return self
```

#### 2.4 Validate `PlusOneSubmit` — non-empty name fields

Same as `GuestInfoSubmit`, email is already `EmailStr` (validated by Pydantic). Add name validators:

```python
class PlusOneSubmit(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    ...

    @field_validator('first_name', 'last_name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('must not be empty')
        return v.strip()
```

---

## 3. Backend Tests

**File:** `src/guests/features/update_rsvp/tests/test_endpoint.py`

### Approach

Follow the existing two-tier pattern:
- **Endpoint tests** (in `test_endpoint.py`): use `InMemoryRSVPWriteModel` + `client_factory` overrides, test the HTTP layer and Pydantic validation. Validation errors never reach the write model, so 422 responses are tested here.
- **Write model tests** (in `src/guests/repository/tests/test_write_model.py`): test database behaviour for valid submissions (existing tests already cover the happy path — no new write model tests needed for validation since invalid payloads are rejected by Pydantic before hitting the model).

### 3.1 Name validation — `GuestInfoSubmit`

```python
UPDATE_RSVP_URL = "/api/v1/guests/{token}/rsvp"

@pytest.mark.asyncio
@pytest.mark.parametrize("field,value", [
    ("first_name", ""),
    ("first_name", "   "),
    ("last_name", ""),
    ("last_name", "   "),
])
async def test_rsvp_rejects_empty_guest_name(client_factory, field, value):
    payload = {
        "attending": True,
        "guest_info": {
            "first_name": "Jan",
            "last_name": "Smit",
            field: value,
        },
        "family_member_updates": {},
    }
    async with client_factory() as client:
        response = await client.post(
            url=UPDATE_RSVP_URL.format(token="test-token"),
            json=payload,
        )
    assert response.status_code == 422
```

### 3.2 Dietary "other" requires notes

```python
@pytest.mark.asyncio
@pytest.mark.parametrize("notes", [None, "", "   "])
async def test_rsvp_rejects_dietary_other_without_notes(client_factory, notes):
    payload = {
        "attending": True,
        "guest_info": {"first_name": "Jan", "last_name": "Smit"},
        "dietary_requirements": [
            {"requirement_type": "other", "notes": notes}
        ],
        "family_member_updates": {},
    }
    async with client_factory() as client:
        response = await client.post(
            url=UPDATE_RSVP_URL.format(token="test-token"),
            json=payload,
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_rsvp_accepts_dietary_other_with_notes(client_factory):
    memory = {}
    write_model = InMemoryRSVPWriteModel(memory)
    payload = {
        "attending": True,
        "guest_info": {"first_name": "Jan", "last_name": "Smit"},
        "dietary_requirements": [
            {"requirement_type": "other", "notes": "no onions"}
        ],
        "family_member_updates": {},
    }
    async with client_factory({get_rsvp_write_model: lambda: write_model}) as client:
        response = await client.post(
            url=UPDATE_RSVP_URL.format(token="test-token"),
            json=payload,
        )
    assert response.status_code == 200
```

### 3.3 Plus-one validation

```python
@pytest.mark.asyncio
@pytest.mark.parametrize("override,value", [
    ("email", "not-an-email"),
    ("email", ""),
    ("first_name", ""),
    ("first_name", "   "),
    ("last_name", ""),
    ("last_name", "   "),
])
async def test_rsvp_rejects_invalid_plus_one(client_factory, override, value):
    plus_one = {
        "email": "plus@example.com",
        "first_name": "Anna",
        "last_name": "Smit",
        override: value,
    }
    payload = {
        "attending": True,
        "guest_info": {"first_name": "Jan", "last_name": "Smit"},
        "plus_one_details": plus_one,
        "family_member_updates": {},
    }
    async with client_factory() as client:
        response = await client.post(
            url=UPDATE_RSVP_URL.format(token="test-token"),
            json=payload,
        )
    assert response.status_code == 422
```

### 3.4 Not attending — plus_one is stripped (no error)

```python
@pytest.mark.asyncio
async def test_rsvp_not_attending_ignores_plus_one(client_factory):
    """plus_one_details sent with attending=false should be accepted and stripped."""
    memory = {}
    write_model = InMemoryRSVPWriteModel(memory)
    payload = {
        "attending": False,
        "guest_info": {"first_name": "Jan", "last_name": "Smit"},
        "plus_one_details": {
            "email": "plus@example.com",
            "first_name": "Anna",
            "last_name": "Smit",
        },
        "family_member_updates": {},
    }
    async with client_factory({get_rsvp_write_model: lambda: write_model}) as client:
        response = await client.post(
            url=UPDATE_RSVP_URL.format(token="test-token"),
            json=payload,
        )
    assert response.status_code == 200
    assert response.json()["attending"] is False
```

---

## 4. E2E Tests (Playwright)

**New file:** `packages/e2e/tests/rsvp-validation.spec.ts`

Playwright is already configured in `packages/e2e/`. Tests run with `pnpm test` from that directory. Follow the patterns established in `rsvp-mocked.spec.ts`: mock both the guest info and RSVP submit endpoints via `page.route()`, use the custom fixtures from `src/fixtures.ts`, and target elements by `id`.

### 4.1 Shared setup

```ts
import { test, expect, Page } from '../src/fixtures';

const TEST_TOKEN = 'test-token-validation';

// Re-use the mock helper pattern from rsvp-mocked.spec.ts
async function mockGuestInfo(page: Page, apiURL: string, token: string) {
  await page.route(`${apiURL}/api/v1/guests/${token}/info`, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        first_name: '',
        last_name: '',
        attending: null,
        dietary_requirements: [],
        allergies: null,
        plus_one_details: null,
        family_members: [],
        bring_a_plus_one: true,
      }),
    })
  );
}

async function fillValidGuestInfo(page: Page) {
  await page.locator('#first_name').fill('Jan');
  await page.locator('#last_name').fill('Smit');
}
```

### 4.2 Test: missing first name shows error

```ts
test('shows error when first name is empty', async ({ page, frontendURL, apiURL, language }) => {
  await mockGuestInfo(page, apiURL, TEST_TOKEN);
  await page.goto(`${frontendURL}/${language}/rsvp?token=${TEST_TOKEN}`);

  await page.locator('#last_name').fill('Smit');
  await page.locator('input[name="attending"][value="yes"]').check();
  await page.locator('button[type="submit"]').click();

  await expect(page.locator('#error-first_name')).not.toBeEmpty();
});
```

### 4.3 Test: missing last name shows error

```ts
test('shows error when last name is empty', async ({ page, frontendURL, apiURL, language }) => {
  await mockGuestInfo(page, apiURL, TEST_TOKEN);
  await page.goto(`${frontendURL}/${language}/rsvp?token=${TEST_TOKEN}`);

  await page.locator('#first_name').fill('Jan');
  await page.locator('input[name="attending"][value="yes"]').check();
  await page.locator('button[type="submit"]').click();

  await expect(page.locator('#error-last_name')).not.toBeEmpty();
});
```

### 4.4 Test: dietary "other" without notes shows error

```ts
test('shows error when dietary "other" has no notes', async ({ page, frontendURL, apiURL, language }) => {
  await mockGuestInfo(page, apiURL, TEST_TOKEN);
  await page.goto(`${frontendURL}/${language}/rsvp?token=${TEST_TOKEN}`);

  await fillValidGuestInfo(page);
  await page.locator('input[name="attending"][value="yes"]').check();
  await page.locator('input[name="dietary"][value="other"]').check();
  // leave dietary_notes empty
  await page.locator('button[type="submit"]').click();

  await expect(page.locator('#error-dietary_notes')).not.toBeEmpty();
});
```

### 4.5 Test: dietary "other" with notes does not show error

```ts
test('no error when dietary "other" has notes', async ({ page, frontendURL, apiURL, language }) => {
  await mockGuestInfo(page, apiURL, TEST_TOKEN);
  // Also mock the submit so the form can complete
  await page.route(`${apiURL}/api/v1/guests/${TEST_TOKEN}/rsvp`, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ message: 'ok', attending: true, status: 'confirmed' }) })
  );
  await page.goto(`${frontendURL}/${language}/rsvp?token=${TEST_TOKEN}`);

  await fillValidGuestInfo(page);
  await page.locator('input[name="attending"][value="yes"]').check();
  await page.locator('input[name="dietary"][value="other"]').check();
  await page.locator('#dietary_notes').fill('no onions');
  await page.locator('button[type="submit"]').click();

  await expect(page.locator('#error-dietary_notes')).toBeEmpty();
});
```

### 4.6 Test: plus-one missing email shows error

```ts
test('shows error when plus one email is missing', async ({ page, frontendURL, apiURL, language }) => {
  await mockGuestInfo(page, apiURL, TEST_TOKEN);
  await page.goto(`${frontendURL}/${language}/rsvp?token=${TEST_TOKEN}`);

  await fillValidGuestInfo(page);
  await page.locator('input[name="attending"][value="yes"]').check();
  await page.locator('input[name="plus_one"]').check();
  await page.locator('#plus_one_first_name').fill('Anna');
  await page.locator('#plus_one_last_name').fill('Smit');
  // leave plus_one_email empty
  await page.locator('button[type="submit"]').click();

  await expect(page.locator('#error-plus_one_email')).not.toBeEmpty();
});
```

### 4.7 Test: plus-one missing names shows errors

```ts
test('shows errors when plus one names are missing', async ({ page, frontendURL, apiURL, language }) => {
  await mockGuestInfo(page, apiURL, TEST_TOKEN);
  await page.goto(`${frontendURL}/${language}/rsvp?token=${TEST_TOKEN}`);

  await fillValidGuestInfo(page);
  await page.locator('input[name="attending"][value="yes"]').check();
  await page.locator('input[name="plus_one"]').check();
  await page.locator('#plus_one_email').fill('anna@example.com');
  // leave first and last name empty
  await page.locator('button[type="submit"]').click();

  await expect(page.locator('#error-plus_one_first_name')).not.toBeEmpty();
  await expect(page.locator('#error-plus_one_last_name')).not.toBeEmpty();
});
```

### 4.8 Test: not attending — no validation errors

```ts
test('not attending submits without triggering conditional validation', async ({ page, frontendURL, apiURL, language }) => {
  await mockGuestInfo(page, apiURL, TEST_TOKEN);
  await page.route(`${apiURL}/api/v1/guests/${TEST_TOKEN}/rsvp`, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ message: 'ok', attending: false, status: 'declined' }) })
  );
  await page.goto(`${frontendURL}/${language}/rsvp?token=${TEST_TOKEN}`);

  await fillValidGuestInfo(page);
  await page.locator('input[name="attending"][value="no"]').check();
  await page.locator('button[type="submit"]').click();

  // All error spans should be empty
  const errorSpans = page.locator('.field-error');
  const count = await errorSpans.count();
  for (let i = 0; i < count; i++) {
    await expect(errorSpans.nth(i)).toBeEmpty();
  }
});
```

### 4.9 Test: errors clear after correction and resubmit

```ts
test('errors are cleared when corrected fields are resubmitted', async ({ page, frontendURL, apiURL, language }) => {
  await mockGuestInfo(page, apiURL, TEST_TOKEN);
  await page.goto(`${frontendURL}/${language}/rsvp?token=${TEST_TOKEN}`);

  // Submit with missing first name to trigger error
  await page.locator('#last_name').fill('Smit');
  await page.locator('input[name="attending"][value="yes"]').check();
  await page.locator('button[type="submit"]').click();
  await expect(page.locator('#error-first_name')).not.toBeEmpty();

  // Fix the field
  await page.locator('#first_name').fill('Jan');
  await page.locator('button[type="submit"]').click();
  await expect(page.locator('#error-first_name')).toBeEmpty();
});
```

---

## 5. Files to Modify / Create

See section 8 for the full consolidated file list.

---

## 6. Plus-One Dietary "Other" Notes Validation

The plus-one form already has its own `plus_one_dietary` checkboxes and a `plus_one_dietary_notes` textarea (conditionally shown when "other" is checked). This follows the exact same pattern as the main guest.

### 6.1 Backend

No extra work needed. `PlusOneSubmit.dietary_requirements` is `list[DietaryRequirement]`, and `DietaryRequirement` already gains the `notes_required_for_other` validator in section 2.2. The constraint is enforced automatically.

Add one backend test to confirm:

```python
@pytest.mark.asyncio
@pytest.mark.parametrize("notes", [None, "", "   "])
async def test_rsvp_rejects_plus_one_dietary_other_without_notes(client_factory, notes):
    payload = {
        "attending": True,
        "guest_info": {"first_name": "Jan", "last_name": "Smit"},
        "plus_one_details": {
            "email": "anna@example.com",
            "first_name": "Anna",
            "last_name": "Smit",
            "dietary_requirements": [{"requirement_type": "other", "notes": notes}],
        },
        "family_member_updates": {},
    }
    async with client_factory() as client:
        response = await client.post(
            url=UPDATE_RSVP_URL.format(token="test-token"),
            json=payload,
        )
    assert response.status_code == 422
```

### 6.2 Frontend

In `validateForm()`, add a block inside the `hasPlusOne` branch (after the name/email checks):

```js
if (hasPlusOne) {
  // ... existing name/email checks ...

  const plusOneDietary = formData.getAll('plus_one_dietary');
  if (plusOneDietary.includes('other') && !formData.get('plus_one_dietary_notes')?.trim()) {
    errors['plus_one_dietary_notes'] = 'Please describe your plus one\'s dietary requirements';
  }
}
```

Add an error span after the `plus_one_dietary_notes` textarea:

```html
<textarea id="plus_one_dietary_notes" name="plus_one_dietary_notes" ...></textarea>
<span id="error-plus_one_dietary_notes" class="field-error" aria-live="polite"></span>
```

### 6.3 E2E test (add to `rsvp-validation.spec.ts`)

```ts
test('shows error when plus one dietary "other" has no notes', async ({ page, frontendURL, apiURL, language }) => {
  await mockGuestInfo(page, apiURL, TEST_TOKEN);
  await page.goto(`${frontendURL}/${language}/rsvp?token=${TEST_TOKEN}`);

  await fillValidGuestInfo(page);
  await page.locator('input[name="attending"][value="yes"]').check();
  await page.locator('input[name="plus_one"]').check();
  await page.locator('#plus_one_email').fill('anna@example.com');
  await page.locator('#plus_one_first_name').fill('Anna');
  await page.locator('#plus_one_last_name').fill('Smit');
  await page.locator('input[name="plus_one_dietary"][value="other"]').check();
  // leave plus_one_dietary_notes empty
  await page.locator('button[type="submit"]').click();

  await expect(page.locator('#error-plus_one_dietary_notes')).not.toBeEmpty();
});
```

---

## 7. i18n for Frontend Error Messages

Error messages in `validateForm()` are currently hardcoded in English. They should use the same translation system as the rest of the RSVP page (`t.rsvpPage.*` keys).

### 7.1 Add translation keys

Add the following keys to all three translation files under the `rsvpPage` object:

**`frontend/src/i18n/en.json`**
```json
"errorFirstNameRequired": "First name is required",
"errorLastNameRequired": "Last name is required",
"errorAttendingRequired": "Please indicate if you will attend",
"errorDietaryNotesRequired": "Please describe your dietary requirements",
"errorPlusOneEmailRequired": "Email is required for your plus one",
"errorPlusOneFirstNameRequired": "First name is required for your plus one",
"errorPlusOneLastNameRequired": "Last name is required for your plus one",
"errorPlusOneDietaryNotesRequired": "Please describe your plus one's dietary requirements"
```

**`frontend/src/i18n/nl.json`**
```json
"errorFirstNameRequired": "Voornaam is verplicht",
"errorLastNameRequired": "Achternaam is verplicht",
"errorAttendingRequired": "Geef aan of je aanwezig zult zijn",
"errorDietaryNotesRequired": "Beschrijf je dieetwensen",
"errorPlusOneEmailRequired": "E-mailadres is verplicht voor je partner",
"errorPlusOneFirstNameRequired": "Voornaam is verplicht voor je partner",
"errorPlusOneLastNameRequired": "Achternaam is verplicht voor je partner",
"errorPlusOneDietaryNotesRequired": "Beschrijf de dieetwensen van je partner"
```

**`frontend/src/i18n/es.json`**
```json
"errorFirstNameRequired": "El nombre es obligatorio",
"errorLastNameRequired": "El apellido es obligatorio",
"errorAttendingRequired": "Indica si asistirás",
"errorDietaryNotesRequired": "Describe tus requisitos dietéticos",
"errorPlusOneEmailRequired": "El correo electrónico es obligatorio para tu acompañante",
"errorPlusOneFirstNameRequired": "El nombre es obligatorio para tu acompañante",
"errorPlusOneLastNameRequired": "El apellido es obligatorio para tu acompañante",
"errorPlusOneDietaryNotesRequired": "Describe los requisitos dietéticos de tu acompañante"
```

### 7.2 Pass translations into the script

The RSVP page already passes `t.rsvpPage` into the inline script via `define:vars`. Extend the existing `define:vars` block to include the new keys (they'll be available on the same `t` object):

```astro
<script define:vars={{ t: t.rsvpPage, apiHost: ... }}>
```

No change to the `define:vars` call is needed — the new keys are automatically part of `t.rsvpPage`.

### 7.3 Update `validateForm()` to use translation keys

Replace the hardcoded English strings with `t.*` references:

```js
function validateForm(formData) {
  const errors = {};

  if (!formData.get('first_name')?.trim())
    errors['first_name'] = t.errorFirstNameRequired;
  if (!formData.get('last_name')?.trim())
    errors['last_name'] = t.errorLastNameRequired;

  const attending = formData.get('attending');
  if (!attending)
    errors['attending'] = t.errorAttendingRequired;

  if (attending === 'yes') {
    const dietary = formData.getAll('dietary');
    if (dietary.includes('other') && !formData.get('dietary_notes')?.trim())
      errors['dietary_notes'] = t.errorDietaryNotesRequired;

    const hasPlusOne = formData.get('plus_one') === 'on';
    if (hasPlusOne) {
      if (!formData.get('plus_one_email')?.trim())
        errors['plus_one_email'] = t.errorPlusOneEmailRequired;
      if (!formData.get('plus_one_first_name')?.trim())
        errors['plus_one_first_name'] = t.errorPlusOneFirstNameRequired;
      if (!formData.get('plus_one_last_name')?.trim())
        errors['plus_one_last_name'] = t.errorPlusOneLastNameRequired;

      const plusOneDietary = formData.getAll('plus_one_dietary');
      if (plusOneDietary.includes('other') && !formData.get('plus_one_dietary_notes')?.trim())
        errors['plus_one_dietary_notes'] = t.errorPlusOneDietaryNotesRequired;
    }
  }

  return errors;
}
```

### 7.4 E2E tests for translated error messages (add to `rsvp-validation.spec.ts`)

The existing tests already verify errors are non-empty. Add two focused tests to confirm the language is respected:

```ts
test('shows error in Dutch when language is nl', async ({ page, frontendURL, apiURL }) => {
  await mockGuestInfo(page, apiURL, TEST_TOKEN);
  await page.goto(`${frontendURL}/nl/rsvp?token=${TEST_TOKEN}`);

  await page.locator('#last_name').fill('Smit');
  await page.locator('input[name="attending"][value="yes"]').check();
  await page.locator('button[type="submit"]').click();

  await expect(page.locator('#error-first_name')).toHaveText('Voornaam is verplicht');
});

test('shows error in Spanish when language is es', async ({ page, frontendURL, apiURL }) => {
  await mockGuestInfo(page, apiURL, TEST_TOKEN);
  await page.goto(`${frontendURL}/es/rsvp?token=${TEST_TOKEN}`);

  await page.locator('#last_name').fill('Smit');
  await page.locator('input[name="attending"][value="yes"]').check();
  await page.locator('button[type="submit"]').click();

  await expect(page.locator('#error-first_name')).toHaveText('El nombre es obligatorio');
});
```

---

## 8. Files to Modify / Create

| File | Change |
|------|--------|
| `frontend/src/pages/[lang]/rsvp/index.astro` | Add error spans, CSS, `validateForm()` with i18n, wire into submit handler; add `plus_one_dietary_notes` error span |
| `src/guests/features/update_rsvp/router.py` | Add Pydantic validators to `GuestInfoSubmit`, `DietaryRequirement`, `PlusOneSubmit`, `RSVPResponseSubmit` |
| `src/guests/features/update_rsvp/tests/test_endpoint.py` | Add validation failure + edge-case tests (sections 3.1–3.4, 6.1) |
| `frontend/src/i18n/en.json` | Add 8 error message keys under `rsvpPage` |
| `frontend/src/i18n/nl.json` | Add 8 error message keys under `rsvpPage` |
| `frontend/src/i18n/es.json` | Add 8 error message keys under `rsvpPage` |
| `packages/e2e/tests/rsvp-validation.spec.ts` | New file — e2e validation test suite (sections 4.2–4.9, 6.3, 7.4) |

---

## 9. Out of Scope

- Family member validation (not requested)
