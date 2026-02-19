# Frontend Testing Guide

**Version:** v1.0.0  
**Last Updated:** 2025-02-17  
**Author**: Frontend Team  
**Review Status**: Approved

## Overview

This document provides comprehensive guidelines for testing the React frontend of the Transformation Coaching platform. It covers unit tests, component tests, integration tests, and end-to-end testing using modern testing tools and best practices.

## Testing Architecture

### Test Structure

```
frontend/src/
├── __tests__/                 # Test files co-located with components
│   ├── components/
│   ├── pages/
│   ├── hooks/
│   ├── utils/
│   └── setup.ts              # Test configuration
├── __mocks__/                 # Mock files
│   └── fileMock.js
├── cypress/                  # E2E tests
│   ├── fixtures/
│   ├── integration/
│   ├── support/
│   └── tsconfig.json
└── jest.config.js           # Jest configuration
```

## Test Configuration

### jest.config.js

```javascript
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/__tests__/setup.ts'],
  moduleNameMapping: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '\\.(jpg|jpeg|png|gif|eot|otf|webp|svg|ttf|woff|woff2|mp4|webm|wav|mp3|m4a|aac|oga)$':
      '<rootDir>/src/__mocks__/fileMock.js',
  },
  transform: {
    '^.+\\.(ts|tsx)$': 'ts-jest',
    '^.+\\.(js|jsx)$': 'babel-jest',
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/index.tsx',
    '!src/reportWebVitals.ts',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{ts,tsx}',
    '<rootDir>/src/**/*.{test,spec}.{ts,tsx}',
  ],
};
```

### src/__tests__/setup.ts

```typescript
import '@testing-library/jest-dom';
import { server } from './mocks/server';

// Establish API mocking before all tests
beforeAll(() => server.listen());

// Reset any request handlers that we may add during the tests,
// so they don't affect other tests
afterEach(() => server.resetHandlers());

// Clean up after the tests are finished
afterAll(() => server.close());

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
};

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
};

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});
```

## Unit Testing

### Component Testing

```typescript
// src/components/Button/__tests__/Button.test.tsx
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '../Button';

describe('Button Component', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });

  it('applies correct variant classes', () => {
    render(<Button variant="primary">Primary Button</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-blue-600');
  });

  it('handles click events', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled when loading', () => {
    render(<Button loading>Loading</Button>);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(screen.getByText('Loading')).toBeInTheDocument();
  });

  it('supports custom className', () => {
    render(<Button className="custom-class">Button</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('custom-class');
  });
});
```

### Hook Testing

```typescript
// src/hooks/__tests__/useAuth.test.ts
import { renderHook, act } from '@testing-library/react';
import { AuthProvider, useAuth } from '../useAuth';
import { server } from '../mocks/server';
import { rest } from 'msw';

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <AuthProvider>{children}</AuthProvider>
);

describe('useAuth Hook', () => {
  it('should initialize with null user', () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    expect(result.current.user).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it('should login successfully', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    
    await act(async () => {
      await result.current.login({
        email: 'test@example.com',
        password: 'password123'
      });
    });

    expect(result.current.user).toEqual({
      id: '1',
      email: 'test@example.com',
      full_name: 'Test User'
    });
    expect(result.current.isLoading).toBe(false);
  });

  it('should handle login errors', async () => {
    server.use(
      rest.post('/api/v1/auth/login', (req, res, ctx) => {
        return res(ctx.status(401), ctx.json({ detail: 'Invalid credentials' }));
      })
    );

    const { result } = renderHook(() => useAuth(), { wrapper });
    
    await act(async () => {
      await expect(
        result.current.login({
          email: 'wrong@example.com',
          password: 'wrong'
        })
      ).rejects.toThrow('Invalid credentials');
    });

    expect(result.current.user).toBeNull();
  });

  it('should logout successfully', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    
    // First login
    await act(async () => {
      await result.current.login({
        email: 'test@example.com',
        password: 'password123'
      });
    });

    // Then logout
    act(() => {
      result.current.logout();
    });

    expect(result.current.user).toBeNull();
  });
});
```

### Utility Function Testing

```typescript
// src/utils/__tests__/validation.test.ts
import { validateEmail, validatePassword, validateWorkoutForm } from '../validation';

describe('Validation Utils', () => {
  describe('validateEmail', () => {
    it('should return true for valid emails', () => {
      expect(validateEmail('test@example.com')).toBe(true);
      expect(validateEmail('user.name+tag@domain.co.uk')).toBe(true);
    });

    it('should return false for invalid emails', () => {
      expect(validateEmail('invalid')).toBe(false);
      expect(validateEmail('@domain.com')).toBe(false);
      expect(validateEmail('user@')).toBe(false);
    });
  });

  describe('validatePassword', () => {
    it('should validate strong passwords', () => {
      const result = validatePassword('StrongPass123!');
      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should reject weak passwords', () => {
      const result = validatePassword('weak');
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain(
        'Password must be at least 8 characters long'
      );
      expect(result.errors).toContain(
        'Password must contain at least one uppercase letter'
      );
    });
  });

  describe('validateWorkoutForm', () => {
    it('should validate complete workout form', () => {
      const form = {
        name: 'Morning Run',
        duration: 30,
        distance: 5,
        description: 'Easy 5km run'
      };
      
      const result = validateWorkoutForm(form);
      expect(result.isValid).toBe(true);
      expect(result.errors).toEqual({});
    });

    it('should return errors for incomplete form', () => {
      const form = {
        name: '',
        duration: 0,
        distance: 0,
        description: ''
      };
      
      const result = validateWorkoutForm(form);
      expect(result.isValid).toBe(false);
      expect(result.errors.name).toBe('Name is required');
      expect(result.errors.duration).toBe('Duration must be greater than 0');
    });
  });
});
```

## Component Integration Testing

### Form Testing

```typescript
// src/components/forms/__tests__/LoginForm.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoginForm } from '../LoginForm';
import { AuthProvider } from '../../../hooks/useAuth';

const renderWithProvider = (component: React.ReactElement) => {
  return render(
    <AuthProvider>
      {component}
    </AuthProvider>
  );
};

describe('LoginForm Integration', () => {
  it('should submit form with valid data', async () => {
    const onLogin = jest.fn();
    renderWithProvider(<LoginForm onLogin={onLogin} />);
    
    // Fill form
    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com');
    await userEvent.type(screen.getByLabelText(/password/i), 'password123');
    
    // Submit form
    await userEvent.click(screen.getByRole('button', { name: /login/i }));
    
    // Verify submission
    await waitFor(() => {
      expect(onLogin).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123'
      });
    });
  });

  it('should show validation errors for empty fields', async () => {
    renderWithProvider(<LoginForm onLogin={jest.fn()} />);
    
    // Submit empty form
    await userEvent.click(screen.getByRole('button', { name: /login/i }));
    
    // Check for errors
    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument();
      expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    });
  });

  it('should toggle password visibility', async () => {
    renderWithProvider(<LoginForm onLogin={jest.fn()} />);
    
    const passwordInput = screen.getByLabelText(/password/i);
    const toggleButton = screen.getByRole('button', { name: /show password/i });
    
    // Initially hidden
    expect(passwordInput).toHaveAttribute('type', 'password');
    
    // Click to show
    await userEvent.click(toggleButton);
    expect(passwordInput).toHaveAttribute('type', 'text');
    expect(toggleButton).toHaveAttribute('aria-label', /hide password/i);
    
    // Click to hide
    await userEvent.click(toggleButton);
    expect(passwordInput).toHaveAttribute('type', 'password');
  });
});
```

### API Integration Testing

```typescript
// src/pages/__tests__/CoachDashboard.test.tsx
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { CoachDashboard } from '../CoachDashboard';
import { AuthProvider } from '../../hooks/useAuth';
import { BrowserRouter } from 'react-router-dom';
import { server } from '../../__tests__/mocks/server';
import { rest } from 'msw';

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        {component}
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('CoachDashboard Integration', () => {
  beforeEach(() => {
    // Mock authenticated user
    localStorage.setItem('access_token', 'mock-token');
  });

  it('should display athlete statistics', async () => {
    renderWithProviders(<CoachDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/total athletes/i)).toBeInTheDocument();
      expect(screen.getByText('15')).toBeInTheDocument();
    });
    
    expect(screen.getByText(/active this month/i)).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
  });

  it('should display recent workouts', async () => {
    renderWithProviders(<CoachDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/recent workouts/i)).toBeInTheDocument();
    });
    
    expect(screen.getByText('Morning Run')).toBeInTheDocument();
    expect(screen.getByText('Evening Ride')).toBeInTheDocument();
  });

  it('should handle API errors gracefully', async () => {
    server.use(
      rest.get('/api/v1/coach/stats', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ error: 'Server error' }));
      })
    );

    renderWithProviders(<CoachDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/failed to load dashboard/i)).toBeInTheDocument();
    });
    
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });
});
```

## Mock Service Worker (MSW) Setup

### API Mocking

```typescript
// src/__tests__/mocks/server.ts
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);
```

```typescript
// src/__tests__/mocks/handlers.ts
import { rest } from 'msw';

const API_BASE = 'http://localhost:8000/api/v1';

export const handlers = [
  // Auth endpoints
  rest.post(`${API_BASE}/auth/login`, (req, res, ctx) => {
    const { email, password } = req.body as any;
    
    if (email === 'test@example.com' && password === 'password123') {
      return res(
        ctx.status(200),
        ctx.json({
          access_token: 'mock-access-token',
          refresh_token: 'mock-refresh-token',
          token_type: 'bearer',
          expires_in: 900,
          user: {
            id: '1',
            email: 'test@example.com',
            full_name: 'Test User',
            role: 'coach'
          }
        })
      );
    }
    
    return res(
      ctx.status(401),
      ctx.json({ detail: 'Incorrect email or password' })
    );
  }),

  // Coach endpoints
  rest.get(`${API_BASE}/coach/stats`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        total_athletes: 15,
        active_athletes: 12,
        workouts_shared: 45,
        imports_this_month: 38
      })
    );
  }),

  rest.get(`${API_BASE}/coach/workouts`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json([
        {
          id: '1',
          name: 'Morning Run',
          sport_type: 'running',
          duration: 1800,
          distance: 5000,
          created_at: '2024-01-15T08:00:00Z'
        },
        {
          id: '2',
          name: 'Evening Ride',
          sport_type: 'cycling',
          duration: 3600,
          distance: 20000,
          created_at: '2024-01-14T18:00:00Z'
        }
      ])
    );
  }),

  // Athlete endpoints
  rest.get(`${API_BASE}/athlete/workouts`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json([
        {
          id: '1',
          workout_name: 'Tempo Run',
          coach_name: 'John Doe',
          shared_at: '2024-01-15T10:00:00Z',
          status: 'pending'
        },
        {
          id: '2',
          workout_name: 'Hill Repeats',
          coach_name: 'John Doe',
          shared_at: '2024-01-14T09:00:00Z',
          status: 'imported'
        }
      ])
    );
  }),
];
```

## End-to-End Testing with Cypress

### Cypress Configuration

```javascript
// cypress.config.ts
import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    supportFile: 'cypress/support/e2e.ts',
    specPattern: 'cypress/integration/**/*.cy.{js,jsx,ts,tsx}',
    video: true,
    screenshotOnRunFailure: true,
    viewportWidth: 1280,
    viewportHeight: 720,
    env: {
      apiUrl: 'http://localhost:8000/api/v1'
    }
  }
});
```

### Custom Commands

```typescript
// cypress/support/commands.ts
import '@testing-library/cypress/add-commands';

declare global {
  namespace Cypress {
    interface Chainable {
      login(email?: string, password?: string): Chainable<void>;
      logout(): Chainable<void>;
      createWorkout(data?: any): Chainable<void>;
      shareWorkout(workoutId: string, athleteIds: string[]): Chainable<void>;
    }
  }
}

Cypress.Commands.add('login', (email = 'coach@example.com', password = 'password123') => {
  cy.visit('/login');
  cy.get('[data-testid="email-input"]').type(email);
  cy.get('[data-testid="password-input"]').type(password);
  cy.get('[data-testid="login-button"]').click();
  cy.url().should('include', '/dashboard');
});

Cypress.Commands.add('logout', () => {
  cy.get('[data-testid="user-menu"]').click();
  cy.get('[data-testid="logout-button"]').click();
  cy.url().should('include', '/login');
});

Cypress.Commands.add('createWorkout', (data = {}) => {
  const defaultData = {
    name: 'Test Workout',
    sport_type: 'running',
    duration: 1800,
    distance: 5000
  };
  
  cy.request({
    method: 'POST',
    url: `${Cypress.env().apiUrl}/workouts`,
    body: { ...defaultData, ...data },
    headers: {
      Authorization: `Bearer ${window.localStorage.getItem('access_token')}`
    }
  }).then((response) => response.body);
});

Cypress.Commands.add('shareWorkout', (workoutId: string, athleteIds: string[]) => {
  cy.request({
    method: 'POST',
    url: `${Cypress.env().apiUrl}/coach/workouts/share`,
    body: {
      workout_ids: [workoutId],
      athlete_ids: athleteIds,
      message: 'Test workout share'
    },
    headers: {
      Authorization: `Bearer ${window.localStorage.getItem('access_token')}`
    }
  });
});
```

### E2E Test Examples

```typescript
// cypress/integration/coach-workflow.cy.ts
describe('Coach Workflow', () => {
  beforeEach(() => {
    cy.login();
  });

  it('should share workout with athlete', () => {
    // Navigate to workouts
    cy.get('[data-testid="workouts-nav"]').click();
    cy.url().should('include', '/workouts');
    
    // Select first workout
    cy.get('[data-testid="workout-item"]').first().within(() => {
      cy.get('[data-testid="select-workout"]').click();
    });
    
    // Open share dialog
    cy.get('[data-testid="share-button"]').click();
    cy.get('[data-testid="share-dialog"]').should('be.visible');
    
    // Select athletes
    cy.get('[data-testid="athlete-select"]').click();
    cy.get('[data-testid="athlete-option"]').first().click();
    cy.get('[data-testid="athlete-option"]').eq(1).click();
    cy.get('[data-testid="athlete-select"]').click(); // Close dropdown
    
    // Add message and share
    cy.get('[data-testid="share-message"]').type('Here is your workout!');
    cy.get('[data-testid="confirm-share"]').click();
    
    // Verify success
    cy.get('[data-testid="success-message"]')
      .should('be.visible')
      .and('contain', 'Workout shared successfully');
  });

  it('should view athlete progress', () => {
    // Navigate to athletes
    cy.get('[data-testid="athletes-nav"]').click();
    
    // Click on first athlete
    cy.get('[data-testid="athlete-card"]').first().click();
    
    // Verify athlete details
    cy.get('[data-testid="athlete-name"]').should('be.visible');
    cy.get('[data-testid="athlete-stats"]').should('be.visible');
    
    // View workout history
    cy.get('[data-testid="workout-history-tab"]').click();
    cy.get('[data-testid="workout-history-item"]').should('have.length.greaterThan', 0);
  });

  it('should connect Garmin account', () => {
    // Navigate to settings
    cy.get('[data-testid="settings-nav"]').click();
    
    // Find Garmin section
    cy.get('[data-testid="garmin-section"]').within(() => {
      cy.get('[data-testid="connect-garmin"]').click();
    });
    
    // Fill credentials
    cy.get('[data-testid="garmin-email"]').type('test@garmin.com');
    cy.get('[data-testid="garmin-password"]').type('garminpass123');
    cy.get('[data-testid="test-connection"]').click();
    
    // Verify success
    cy.get('[data-testid="connection-success"]')
      .should('be.visible')
      .and('contain', 'Successfully connected');
  });
});
```

```typescript
// cypress/integration/athlete-workflow.cy.ts
describe('Athlete Workflow', () => {
  beforeEach(() => {
    cy.login('athlete@example.com', 'password123');
  });

  it('should import shared workout', () => {
    // Navigate to dashboard
    cy.url().should('include', '/dashboard');
    
    // Find new workout
    cy.get('[data-testid="new-workout-card"]').within(() => {
      cy.get('[data-testid="workout-name"]').should('contain', 'Tempo Run');
      cy.get('[data-testid="import-button"]').click();
    });
    
    // Confirm import
    cy.get('[data-testid="confirm-import"]').click();
    
    // Verify success
    cy.get('[data-testid="import-success"]')
      .should('be.visible')
      .and('contain', 'Workout imported successfully');
    
    // Check it's in imported list
    cy.get('[data-testid="imported-workouts"]').within(() => {
      cy.get('[data-testid="workout-item"]').should('contain', 'Tempo Run');
    });
  });

  it('should view workout details before importing', () => {
    // Click on workout
    cy.get('[data-testid="new-workout-card"]').first().click();
    
    // Verify details modal
    cy.get('[data-testid="workout-details-modal"]').should('be.visible');
    cy.get('[data-testid="workout-name"]').should('be.visible');
    cy.get('[data-testid="workout-duration"]').should('be.visible');
    cy.get('[data-testid="workout-steps"]').should('be.visible');
    
    // Close modal
    cy.get('[data-testid="close-modal"]').click();
    cy.get('[data-testid="workout-details-modal"]').should('not.exist');
  });
});
```

## Visual Regression Testing

### Chromatic Configuration

```typescript
// .storybook/main.ts
import type { StorybookConfig } from '@storybook/react';

const config: StorybookConfig = {
  stories: ['../src/**/*.stories.@(js|jsx|ts|tsx)'],
  addons: [
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
    'chromatic/storybook-addon'
  ],
  framework: {
    name: '@storybook/react-webpack5',
    options: {}
  }
};

export default config;
```

### Storybook Stories

```typescript
// src/components/Button/Button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta: Meta<typeof Button> = {
  title: 'Components/Button',
  component: Button,
  parameters: {
    layout: 'centered',
    chromatic: { disableSnapshot: false }
  },
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'outline']
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg']
    }
  }
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Primary Button'
  }
};

export const Secondary: Story = {
  args: {
    variant: 'secondary',
    children: 'Secondary Button'
  }
};

export const Outline: Story = {
  args: {
    variant: 'outline',
    children: 'Outline Button'
  }
};

export const Loading: Story = {
  args: {
    variant: 'primary',
    loading: true,
    children: 'Loading'
  }
};
```

## Accessibility Testing

### axe-core Integration

```typescript
// src/__tests__/accessibility/accessibility.test.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { Dashboard } from '../../pages/Dashboard';

expect.extend(toHaveNoViolations);

describe('Accessibility', () => {
  it('should not have accessibility violations', async () => {
    const { container } = render(<Dashboard />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should support keyboard navigation', () => {
    render(<Dashboard />);
    
    // Tab through interactive elements
    const body = document.body;
    body.focus();
    
    // First tab should focus on skip link
    expect(document.activeElement).toHaveAttribute('href', '#main');
    
    // Continue tabbing
    fireEvent.keyDown(body, { key: 'Tab' });
    expect(document.activeElement).toHaveAttribute('data-testid', 'main-nav');
  });

  it('should have proper ARIA labels', () => {
    render(<Dashboard />);
    
    // Check for proper landmarks
    expect(screen.getByRole('banner')).toBeInTheDocument(); // <header>
    expect(screen.getByRole('navigation')).toBeInTheDocument(); // <nav>
    expect(screen.getByRole('main')).toBeInTheDocument(); // <main>
    expect(screen.getByRole('contentinfo')).toBeInTheDocument(); // <footer>
    
    // Check for form labels
    const inputs = screen.getAllByRole('textbox');
    inputs.forEach(input => {
      expect(input).toHaveAttribute('aria-label');
    });
  });
});
```

### Cypress Accessibility Testing

```typescript
// cypress/integration/accessibility.cy.ts
describe('Accessibility Tests', () => {
  beforeEach(() => {
    cy.injectAxe();
  });

  it('should not have accessibility violations on login page', () => {
    cy.visit('/login');
    cy.checkA11y();
  });

  it('should not have accessibility violations on dashboard', () => {
    cy.login();
    cy.checkA11y();
  });

  it('should support keyboard navigation', () => {
    cy.visit('/login');
    
    // Tab through form
    cy.get('body').tab();
    cy.focused().should('have.attr', 'data-testid', 'email-input');
    
    cy.focused().tab();
    cy.focused().should('have.attr', 'data-testid', 'password-input');
    
    cy.focused().tab();
    cy.focused().should('have.attr', 'data-testid', 'login-button');
  });

  it('should have proper color contrast', () => {
    cy.visit('/');
    
    // Check specific elements for contrast
    cy.get('[data-testid="primary-button"]')
      .should('have.css', 'color')
      .and('match', /^rgb/);
    
    // This would need custom implementation for actual contrast checking
    // Consider using cypress-axe with color-contrast rules
  });
});
```

## Performance Testing

### Component Performance

```typescript
// src/__tests__/performance/WorkoutList.performance.test.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import { WorkoutList } from '../../components/WorkoutList';
import { act } from 'react-test-renderer';

describe('WorkoutList Performance', () => {
  const generateWorkouts = (count: number) => {
    return Array.from({ length: count }, (_, i) => ({
      id: `workout-${i}`,
      name: `Workout ${i}`,
      duration: 1800,
      distance: 5000,
      created_at: new Date().toISOString()
    }));
  };

  it('should render 1000 workouts efficiently', () => {
    const workouts = generateWorkouts(1000);
    
    const startTime = performance.now();
    
    render(<WorkoutList workouts={workouts} />);
    
    const endTime = performance.now();
    const renderTime = endTime - startTime;
    
    // Should render within 100ms
    expect(renderTime).toBeLessThan(100);
    expect(screen.getAllByTestId('workout-item')).toHaveLength(1000);
  });

  it('should not re-render unnecessarily', () => {
    const workouts = generateWorkouts(100);
    const { rerender } = render(<WorkoutList workouts={workouts} />);
    
    const renderSpy = jest.fn();
    WorkoutList.prototype.render = renderSpy;
    
    // Re-render with same props
    rerender(<WorkoutList workouts={workouts} />);
    
    // Should not re-render if props haven't changed
    // Note: This is a simplified example, real implementation would use React.memo
  });
});
```

### Lighthouse CI Integration

```yaml
# .lighthouserc.js
module.exports = {
  ci: {
    collect: {
      url: ['http://localhost:3000'],
      startServerCommand: 'npm start',
      startServerReadyPattern: 'Compiled successfully!',
      startServerReadyTimeout: 30000,
    },
    assert: {
      assertions: {
        'categories:performance': ['warn', { minScore: 0.8 }],
        'categories:accessibility': ['error', { minScore: 0.9 }],
        'categories:best-practices': ['warn', { minScore: 0.8 }],
        'categories:seo': ['warn', { minScore: 0.8 }],
      },
    },
    upload: {
      target: 'temporary-public-storage',
    },
  },
};
```

## Test Execution

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm test -- WorkoutList.test.tsx

# Run tests matching pattern
npm test -- --testNamePattern="should render"

# Run E2E tests
npm run test:e2e

# Run E2E tests headed
npm run test:e2e:headed

# Run accessibility tests
npm run test:a11y

# Run performance tests
npm run test:performance
```

### Package.json Scripts

```json
{
  "scripts": {
    "test": "react-scripts test",
    "test:coverage": "react-scripts test --coverage --watchAll=false",
    "test:e2e": "cypress run",
    "test:e2e:open": "cypress open",
    "test:e2e:headed": "cypress run --headed",
    "test:a11y": "jest --testPathPattern=accessibility",
    "test:performance": "jest --testPathPattern=performance",
    "test:visual": "chromatic test --build-script-name build",
    "test:all": "npm run test:coverage && npm run test:e2e && npm run test:a11y"
  }
}
```

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/frontend-tests.yml
name: Frontend Tests

on:
  push:
    branches: [ main, develop ]
    paths: [ 'frontend/**' ]
  pull_request:
    branches: [ main ]
    paths: [ 'frontend/**' ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
    
    - name: Install dependencies
      run: |
        cd frontend
        npm ci
    
    - name: Run linting
      run: |
        cd frontend
        npm run lint
    
    - name: Run unit tests
      run: |
        cd frontend
        npm run test:coverage
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: frontend/coverage/lcov.info
        flags: frontend
    
    - name: Build application
      run: |
        cd frontend
        npm run build
    
    - name: Run E2E tests
      run: |
        cd frontend
        npm start & 
        sleep 30
        npm run test:e2e
    
    - name: Run accessibility tests
      run: |
        cd frontend
        npm run test:a11y
    
    - name: Run visual tests
      run: |
        cd frontend
        npm run test:visual
      env:
        CHROMATIC_PROJECT_TOKEN: ${{ secrets.CHROMATIC_PROJECT_TOKEN }}
```

## Best Practices

### Test Organization

1. **Co-locate tests with components**
2. **Use descriptive test names**
3. **Group related tests with describe**
4. **Use beforeEach for setup**
5. **Keep tests independent**

### Example of Well-structured Test

```typescript
describe('WorkoutCard Component', () => {
  const defaultProps = {
    workout: {
      id: '1',
      name: 'Morning Run',
      duration: 1800,
      distance: 5000,
      created_at: '2024-01-15T08:00:00Z'
    },
    onSelect: jest.fn(),
    onShare: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should display workout information correctly', () => {
    render(<WorkoutCard {...defaultProps} />);
    
    expect(screen.getByText('Morning Run')).toBeInTheDocument();
    expect(screen.getByText('30 minutes')).toBeInTheDocument();
    expect(screen.getByText('5.0 km')).toBeInTheDocument();
  });

  it('should call onSelect when clicked', () => {
    render(<WorkoutCard {...defaultProps} />);
    
    fireEvent.click(screen.getByRole('button', { name: /select workout/i }));
    
    expect(defaultProps.onSelect).toHaveBeenCalledWith(defaultProps.workout);
  });

  it('should show loading state when sharing', () => {
    render(<WorkoutCard {...defaultProps} isSharing />);
    
    expect(screen.getByText('Sharing...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /share/i })).toBeDisabled();
  });
});
```

### Mock Best Practices

1. **Mock at the API level, not component level**
2. **Use MSW for API mocking**
3. **Keep mocks close to real responses**
4. **Reset mocks between tests**

### Performance Best Practices

1. **Use React.memo for expensive components**
2. **Implement virtual scrolling for long lists**
3. **Lazy load components and routes**
4. **Optimize re-renders with useMemo/useCallback**

## Troubleshooting

### Common Issues

1. **Act warnings**
   ```typescript
   // Wrong
   fireEvent.click(screen.getByText('Submit'));
   expect(screen.getByText('Success')).toBeInTheDocument();
   
   // Correct
   fireEvent.click(screen.getByText('Submit'));
   await waitFor(() => {
     expect(screen.getByText('Success')).toBeInTheDocument();
   });
   ```

2. **Mock not working**
   ```typescript
   // Make sure to import the mock before the component
   import { server } from './mocks/server';
   
   beforeAll(() => server.listen());
   afterEach(() => server.resetHandlers());
   ```

3. **Flaky tests**
   ```typescript
   // Add proper waits
   await waitFor(() => {
     expect(element).toBeVisible();
   }, { timeout: 5000 });
   ```

## Test Metrics and Reporting

### Coverage Reports

```bash
# Generate detailed coverage
npm run test:coverage

# View coverage report
open frontend/coverage/lcov-report/index.html
```

### Performance Metrics

```typescript
// Add performance tracking to tests
it('should render within performance budget', async () => {
  const start = performance.now();
  
  render(<ExpensiveComponent data={largeDataSet} />);
  
  await waitFor(() => {
    expect(screen.getByTestId('loaded-content')).toBeInTheDocument();
  });
  
  const duration = performance.now() - start;
  expect(duration).toBeLessThan(100); // 100ms budget
});
```

### Accessibility Metrics

```bash
# Generate accessibility report
npm run test:a11y -- --reporter=json > a11y-report.json
```

## Future Enhancements

### Advanced Testing Strategies

1. **Contract Testing** with Pact
2. **Visual Testing** with Percy
3. **Component Testing** with Storybook
4. **Mutation Testing** with Stryker
5. **AI-powered Test Generation**

### Tool Upgrades

1. **Migrate to Vitest** for faster unit tests
2. **Playwright** as alternative to Cypress
3. **Testing Library** updates
4. **MSW 2.0** features
5. **Enhanced mocking strategies**
