# Frontend Testing

## Setup

The project uses **Vitest** and **React Testing Library** for testing.

### Installation

```bash
npm install
```

## Running Tests

```bash
# Run all tests once
npm test

# Run tests in watch mode
npm run test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

## Test Files

- `src/test/setup.js` - Test configuration and global setup
- `src/test/ConsentBanner.test.jsx` - Tests for GDPR consent banner
- `src/test/UploadForm.test.jsx` - Tests for CV upload and job description form
- `src/test/Results.test.jsx` - Tests for ATS analysis results display
- `src/test/App.test.jsx` - Integration tests for main App component

## Test Coverage

### ConsentBanner Component
- ✅ Renders consent banner with privacy information
- ✅ Shows/hides details on button click
- ✅ Calls onAccept callback when accept button is clicked
- ✅ Displays GDPR compliance information

### UploadForm Component
- ✅ Renders all form fields (CV upload, job description, LinkedIn URL)
- ✅ Shows validation errors for missing required fields
- ✅ Toggles between text input and URL input for job descriptions
- ✅ Uploads files and submits form data to API
- ✅ Handles API errors gracefully
- ✅ Disables form inputs when disabled prop is true

### Results Component
- ✅ Displays overall ATS match score
- ✅ Shows appropriate messages based on score ranges
- ✅ Renders score breakdown for all metrics
- ✅ Displays matched and missing keywords
- ✅ Shows seniority analysis explanation
- ✅ Renders actionable recommendations
- ✅ Applies correct color coding for different score ranges

### App Component
- ✅ Renders main application with header and footer
- ✅ Shows consent banner on first visit
- ✅ Persists consent in localStorage
- ✅ Hides consent banner after acceptance
- ✅ Displays upload form after consent

## Writing New Tests

Example test structure:

```javascript
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import MyComponent from '../components/MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText(/Hello World/i)).toBeInTheDocument()
  })
})
```

## Mocking

### Mocking axios

```javascript
import { vi } from 'vitest'
import axios from 'axios'

vi.mock('axios')

axios.post.mockResolvedValueOnce({ data: { success: true } })
```

### Mocking localStorage

```javascript
beforeEach(() => {
  localStorage.clear()
})

localStorage.setItem('key', 'value')
```

## Best Practices

1. **Use Testing Library queries in this order**:
   - `getByRole` (preferred)
   - `getByLabelText`
   - `getByPlaceholderText`
   - `getByText`
   - `container.querySelector` (last resort)

2. **Test user behavior, not implementation**
   - Test what the user sees and does
   - Avoid testing internal state or implementation details

3. **Use async utilities for async operations**
   - `waitFor` for async updates
   - `userEvent` for simulating user interactions

4. **Clean up after each test**
   - Vitest automatically cleans up DOM
   - Clear mocks in `beforeEach`

## Troubleshooting

### Tests failing with "element not found"
- Check if element is async and needs `waitFor`
- Verify the exact text/regex matches what's rendered
- Use `screen.debug()` to see the rendered output

### File input tests
- File inputs have accessibility limitations
- Use `container.querySelector('input[type="file"]')` instead of `getByLabelText`

### Axios mocks not working
- Ensure `vi.mock('axios')` is at the top level
- Clear mocks in `beforeEach`
- Check mock return values match expected format
