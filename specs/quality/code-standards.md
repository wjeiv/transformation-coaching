# Code Standards

**Version:** v1.0.0  
**Last Updated:** 2025-02-17  
**Author**: Development Team  
**Review Status**: Approved

## Overview

This document defines the coding standards and best practices for the Transformation Coaching platform. Adhering to these standards ensures code quality, maintainability, and consistency across the entire codebase.

## Philosophy

Our coding philosophy is based on:

1. **Readability First**: Code is read more often than it's written
2. **Consistency**: Uniform style makes code easier to understand
3. **Simplicity**: Favor simple solutions over complex ones
4. **Testability**: Code should be easy to test
5. **Documentation**: Code should explain itself when possible

## Python Standards (Backend)

### Code Style

We follow **PEP 8** with some modifications:

```python
# Imports at the top
import asyncio
from datetime import date, datetime
from typing import List, Optional, Union

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse


# Class names: PascalCase
class UserService:
    """Service layer for user operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # Method names: snake_case
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user with validation.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user instance
            
        Raises:
            ValueError: If email already exists
        """
        # Check existing user
        existing = await self.db.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Email already registered")
        
        # Create user
        user = User(**user_data.dict())
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        return user


# Constants: UPPER_SNAKE_CASE
MAX_LOGIN_ATTEMPTS = 5
DEFAULT_PAGE_SIZE = 20
JWT_ALGORITHM = "HS256"


# Function names: snake_case
async def validate_password_strength(password: str) -> bool:
    """Validate password meets security requirements.
    
    Args:
        password: Password to validate
        
    Returns:
        True if password meets requirements
    """
    if len(password) < 8:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    return all([has_upper, has_lower, has_digit, has_special])
```

### Type Hints

All functions must have type hints:

```python
from typing import List, Optional, Dict, Any, Union
from uuid import UUID

def process_workout_data(
    workout_id: UUID,
    user_id: UUID,
    data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Process workout data and return results.
    
    Args:
        workout_id: Unique workout identifier
        user_id: User requesting the processing
        data: Raw workout data
        
    Returns:
        Processed data or None if processing fails
    """
    # Implementation
    pass

# Use generics for better type safety
from typing import TypeVar, Generic

T = TypeVar('T')

class ResponseWrapper(Generic[T]):
    def __init__(self, data: T, message: str):
        self.data = data
        self.message = message
```

### Error Handling

```python
# Custom exceptions
class TransformationCoachingError(Exception):
    """Base exception for the application."""
    pass

class AuthenticationError(TransformationCoachingError):
    """Authentication related errors."""
    pass

class GarminConnectionError(TransformationCoachingError):
    """Garmin API connection errors."""
    def __init__(self, message: str, status_code: int = None):
        self.status_code = status_code
        super().__init__(message)

# Error handling in services
async def share_workout(
    self,
    workout_id: str,
    athlete_ids: List[str]
) -> List[SharedWorkout]:
    """Share workout with multiple athletes."""
    try:
        workout = await self.get_workout(workout_id)
        if not workout:
            raise ValueError("Workout not found")
        
        shared_workouts = []
        for athlete_id in athlete_ids:
            try:
                shared = await self._share_with_athlete(workout, athlete_id)
                shared_workouts.append(shared)
            except Exception as e:
                # Log error but continue with other athletes
                logger.error(f"Failed to share with {athlete_id}: {e}")
                continue
        
        return shared_workouts
        
    except ValueError as e:
        # Re-raise validation errors
        raise
    except Exception as e:
        # Wrap unexpected errors
        logger.exception("Unexpected error in share_workout")
        raise TransformationCoachingError("Failed to share workout") from e
```

### Docstrings

We use Google-style docstrings:

```python
def calculate_workout_pace(
    distance_km: float,
    duration_seconds: int,
    include_units: bool = True
) -> Union[str, float]:
    """Calculate running pace from distance and duration.
    
    Args:
        distance_km: Distance in kilometers
        duration_seconds: Duration in seconds
        include_units: Whether to include min/km in result
        
    Returns:
        Pace in minutes per kilometer as float or formatted string
        
    Raises:
        ValueError: If distance or duration is not positive
        
    Example:
        >>> calculate_workout_pace(5.0, 1800)
        '6:00 min/km'
        >>> calculate_workout_pace(10.0, 3600, False)
        6.0
    """
    if distance_km <= 0 or duration_seconds <= 0:
        raise ValueError("Distance and duration must be positive")
    
    pace_seconds = duration_seconds / distance_km
    pace_minutes = pace_seconds / 60
    
    if include_units:
        minutes = int(pace_minutes)
        seconds = int((pace_minutes - minutes) * 60)
        return f"{minutes}:{seconds:02d} min/km"
    
    return pace_minutes
```

### Database Models

```python
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

class BaseModel:
    """Base model with common fields."""
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

class User(Base, BaseModel):
    """User model representing application users."""
    
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="athlete")
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    workouts = relationship("Workout", back_populates="user")
    shared_workouts = relationship("SharedWorkout", foreign_keys="SharedWorkout.coach_id")
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"
```

### API Endpoints

```python
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_user, get_db

router = APIRouter(prefix="/api/v1/workouts", tags=["workouts"])

@router.get("/", response_model=List[WorkoutResponse])
async def get_workouts(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    sport_type: Optional[str] = Query(None, description="Filter by sport type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[WorkoutResponse]:
    """Get pag workouts for the current user.
    
    Args:
        page: Page number for pagination
        size: Number of items per page
        sport_type: Optional filter by sport type
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List of workouts
    """
    workout_service = WorkoutService(db)
    workouts = await workout_service.get_user_workouts(
        user_id=current_user.id,
        page=page,
        size=size,
        sport_type=sport_type
    )
    
    return [WorkoutResponse.from_orm(w) for w in workouts]

@router.post("/", response_model=WorkoutResponse, status_code=status.HTTP_201_CREATED)
async def create_workout(
    workout_data: WorkoutCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> WorkoutResponse:
    """Create a new workout.
    
    Args:
        workout_data: Workout creation data
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Created workout
        
    Raises:
        HTTPException: If validation fails
    """
    if current_user.role != "coach":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only coaches can create workouts"
        )
    
    workout_service = WorkoutService(db)
    workout = await workout_service.create_workout(
        user_id=current_user.id,
        workout_data=workout_data
    )
    
    return WorkoutResponse.from_orm(workout)
```

## TypeScript/React Standards (Frontend)

### Code Style

We use **Prettier** with specific configurations:

```typescript
// Interfaces and Types
interface User {
  id: string;
  email: string;
  fullName: string;
  role: 'admin' | 'coach' | 'athlete';
  isActive: boolean;
  createdAt: string;
}

// Use type guards for type narrowing
function isAdmin(user: User): user is User & { role: 'admin' } {
  return user.role === 'admin';
}

// Enums for constants
enum UserRole {
  ADMIN = 'admin',
  COACH = 'coach',
  ATHLETE = 'athlete',
}

enum WorkoutStatus {
  PENDING = 'pending',
  SHARED = 'shared',
  IMPORTED = 'imported',
  FAILED = 'failed',
}

// Component Props Interface
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
}

// Functional Component with TypeScript
const Button: React.FC<ButtonProps> = ({
  variant,
  size = 'md',
  disabled = false,
  loading = false,
  children,
  onClick,
  className = '',
}) => {
  const baseClasses = 'font-medium rounded-lg transition-colors focus:outline-none focus:ring-2';
  
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
    outline: 'border-2 border-blue-600 text-blue-600 hover:bg-blue-50 focus:ring-blue-500',
  };
  
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };
  
  return (
    <button
      className={`
        ${baseClasses}
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${disabled || loading ? 'opacity-50 cursor-not-allowed' : ''}
        ${className}
      `}
      disabled={disabled || loading}
      onClick={onClick}
    >
      {loading ? <Spinner size="sm" /> : children}
    </button>
  );
};
```

### Custom Hooks

```typescript
// Custom hook with TypeScript
import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

interface UseApiResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

function useApi<T>(url: string): UseApiResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get<T>(url);
      setData(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [url]);
  
  useEffect(() => {
    fetchData();
  }, [fetchData]);
  
  return { data, loading, error, refetch: fetchData };
}

// Usage example
const WorkoutList: React.FC = () => {
  const { data: workouts, loading, error, refetch } = useApi<Workout[]>('/workouts');
  
  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;
  if (!workouts) return null;
  
  return (
    <div>
      {workouts.map(workout => (
        <WorkoutCard key={workout.id} workout={workout} />
      ))}
    </div>
  );
};
```

### Context Providers

```typescript
// Auth Context with TypeScript
interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  register: (userData: RegisterData) => Promise<void>;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      setToken(token);
      // Verify token and get user
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      getCurrentUser();
    } else {
      setLoading(false);
    }
  }, []);
  
  const login = async (credentials: LoginCredentials): Promise<void> => {
    try {
      const response = await api.post<AuthResponse>('/auth/login', credentials);
      const { access_token, refresh_token, user: userData } = response.data;
      
      setToken(access_token);
      setUser(userData);
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    } catch (error) {
      throw new Error('Login failed');
    }
  };
  
  const logout = (): void => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    delete api.defaults.headers.common['Authorization'];
  };
  
  const value: AuthContextType = {
    user,
    token,
    login,
    logout,
    register: async (userData: RegisterData) => {
      // Implementation
    },
    loading,
  };
  
  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
```

### Service Layer

```typescript
// API Service with Axios interceptors
import axios, { AxiosInstance, AxiosResponse } from 'axios';

class ApiService {
  private client: AxiosInstance;
  
  constructor() {
    this.client = axios.create({
      baseURL: process.env.REACT_APP_API_URL,
      timeout: 10000,
    });
    
    this.setupInterceptors();
  }
  
  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
    
    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            const refreshToken = localStorage.getItem('refresh_token');
            const response = await axios.post('/auth/refresh', {
              refresh_token: refreshToken,
            });
            
            const { access_token } = response.data;
            localStorage.setItem('access_token', access_token);
            
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
            return this.client(originalRequest);
          } catch (refreshError) {
            // Refresh failed, logout user
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
          }
        }
        
        return Promise.reject(error);
      }
    );
  }
  
  // Typed API methods
  async get<T>(url: string, config?: any): Promise<AxiosResponse<T>> {
    return this.client.get(url, config);
  }
  
  async post<T>(url: string, data?: any, config?: any): Promise<AxiosResponse<T>> {
    return this.client.post(url, data, config);
  }
  
  async put<T>(url: string, data?: any, config?: any): Promise<AxiosResponse<T>> {
    return this.client.put(url, data, config);
  }
  
  async delete<T>(url: string, config?: any): Promise<AxiosResponse<T>> {
    return this.client.delete(url, config);
  }
}

export const api = new ApiService();
```

## Testing Standards

### Python Tests

```python
# Test class organization
class TestUserService:
    """Test cases for UserService."""
    
    @pytest.fixture
    def user_service(self, db_session):
        """Create user service with test database."""
        return UserService(db_session)
    
    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing."""
        return {
            "email": "test@example.com",
            "password": "TestPass123!",
            "full_name": "Test User"
        }
    
    async def test_create_user_success(self, user_service, sample_user_data):
        """Test successful user creation."""
        # Arrange
        # - sample_user_data fixture provides data
        
        # Act
        user = await user_service.create_user(sample_user_data)
        
        # Assert
        assert user.email == sample_user_data["email"]
        assert user.full_name == sample_user_data["full_name"]
        assert user.role == UserRole.ATHLETE
        assert user.is_active is True
        assert user.is_verified is False
    
    async def test_create_user_duplicate_email(self, user_service, sample_user_data):
        """Test user creation with duplicate email raises error."""
        # Arrange
        await user_service.create_user(sample_user_data)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Email already registered"):
            await user_service.create_user(sample_user_data)
    
    @pytest.mark.parametrize("password,expected", [
        ("Short1!", False),  # Too short
        ("nouppercase1!", False),  # No uppercase
        ("NOLOWERCASE1!", False),  # No lowercase
        ("NoNumbers!", False),  # No numbers
        ("NoSpecial123", False),  # No special character
        ("ValidPass123!", True),  # Valid
    ])
    async def test_password_validation(self, password: str, expected: bool):
        """Test password validation with various inputs."""
        result = await validate_password_strength(password)
        assert result == expected
```

### React Tests

```typescript
// Component testing with React Testing Library
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { WorkoutCard } from './WorkoutCard';
import { AuthProvider } from '../hooks/useAuth';

// Test utilities
const renderWithProviders = (ui: React.ReactElement) => {
  return render(
    <AuthProvider>
      {ui}
    </AuthProvider>
  );
};

describe('WorkoutCard', () => {
  const mockWorkout: Workout = {
    id: '1',
    name: 'Morning Run',
    sportType: 'running',
    duration: 1800,
    distance: 5000,
    createdAt: '2024-01-15T08:00:00Z',
  };
  
  const defaultProps = {
    workout: mockWorkout,
    onSelect: jest.fn(),
    onShare: jest.fn(),
  };
  
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  it('renders workout information correctly', () => {
    renderWithProviders(<WorkoutCard {...defaultProps} />);
    
    expect(screen.getByText('Morning Run')).toBeInTheDocument();
    expect(screen.getByText('30 minutes')).toBeInTheDocument();
    expect(screen.getByText('5.0 km')).toBeInTheDocument();
    expect(screen.getByText('running')).toBeInTheDocument();
  });
  
  it('calls onSelect when select button is clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<WorkoutCard {...defaultProps} />);
    
    await user.click(screen.getByRole('button', { name: /select/i }));
    
    expect(defaultProps.onSelect).toHaveBeenCalledWith(mockWorkout);
  });
  
  it('shows loading state when sharing', () => {
    renderWithProviders(<WorkoutCard {...defaultProps} isSharing />);
    
    expect(screen.getByText('Sharing...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /share/i })).toBeDisabled();
  });
  
  it('should be accessible', () => {
    renderWithProviders(<WorkoutCard {...defaultProps} />);
    
    // Check for proper ARIA labels
    expect(screen.getByRole('article')).toHaveAttribute('aria-label', 'Morning Run workout');
    
    // Check keyboard navigation
    const selectButton = screen.getByRole('button', { name: /select/i });
    selectButton.focus();
    expect(selectButton).toHaveFocus();
  });
});
```

## Documentation Standards

### Code Comments

```python
# Python comment examples

# Inline comments should explain why, not what
user.is_active = False  # Deactivate instead of deleting for audit trail

# Block comments for complex logic
# Calculate pace using the formula:
# pace = total_time / distance
# Convert to minutes per kilometer for display
pace_seconds = duration_seconds / distance_km
pace_minutes = pace_seconds / 60

# TODO comments with actionable items
# TODO: Implement caching for workout queries
# FIXME: Handle edge case when distance is zero
# NOTE: This algorithm has O(n^2) complexity, optimize for large datasets
```

```typescript
// TypeScript comment examples

// JSDoc for functions
/**
 * Formats a duration in seconds to a human-readable string
 * @param seconds - Duration in seconds
 * @param includeSeconds - Whether to include seconds in output
 * @returns Formatted duration string (e.g., "1h 30m" or "1h 30m 45s")
 */
function formatDuration(seconds: number, includeSeconds = false): string {
  // Implementation
}

// Complex logic explanation
// We use a debounce here to prevent excessive API calls
// while the user is typing. The 300ms delay provides
// a good balance between responsiveness and efficiency.
const debouncedSearch = useMemo(
  () => debounce((query: string) => {
    searchWorkouts(query);
  }, 300),
  []
);
```

### README Standards

Each module/package should have a README with:

```markdown
# Module Name

Brief description of the module's purpose.

## Usage

```python
# Example usage
from app.services.user import UserService

service = UserService(db)
user = await service.create_user(user_data)
```

## API

### UserService.create_user

Create a new user with validation.

**Parameters:**
- `user_data` (UserCreate): User creation data

**Returns:**
- `User`: Created user instance

**Raises:**
- `ValueError`: If email already exists

## Testing

Run tests with:
```bash
pytest tests/test_user_service.py
```

## Dependencies

- SQLAlchemy 2.0+
- Pydantic 2.0+
```

## Git Standards

### Commit Messages

We follow the Conventional Commits specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(auth): add Google OAuth integration

Implement OAuth 2.0 flow with Google for user authentication.
Users can now register/login using their Google account.

Closes #123
```

```
fix(workout): handle zero distance in pace calculation

Add validation to prevent division by zero when calculating
pace for workouts with no distance data.
```

### Branch Naming

```
feature/description
bugfix/description
hotfix/description
release/version
```

Examples:
```
feature/garmin-integration
bugfix/login-validation-error
hotfix/security-patch
release/v1.2.0
```

## Code Review Standards

### Review Checklist

#### Functionality
- [ ] Code works as intended
- [ ] Edge cases are handled
- [ ] Error handling is appropriate
- [ ] Tests cover new functionality

#### Code Quality
- [ ] Code is readable and understandable
- [ ] Follows coding standards
- [ ] No hardcoded values
- [ ] Proper documentation

#### Performance
- [ ] No obvious performance issues
- [ ] Database queries are optimized
- [ ] No memory leaks
- [ ] Appropriate caching

#### Security
- [ ] No security vulnerabilities
- [ ] Input validation
- [ ] Proper authentication/authorization
- [ ] No sensitive data exposed

### Review Process

1. **Self-Review**
   - Review your own code before submitting
   - Run all tests
   - Check code coverage
   - Verify functionality

2. **Peer Review**
   - At least one other developer must review
   - Use the checklist above
   - Provide constructive feedback
   - Discuss suggestions

3. **Approval**
   - Address all review comments
   - Update code as needed
   - Get final approval
   - Merge to main branch

## Linting and Formatting

### Python

```bash
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.950
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### TypeScript

```json
// .eslintrc.json
{
  "extends": [
    "react-app",
    "react-app/jest",
    "@typescript-eslint/recommended",
    "prettier"
  ],
  "parser": "@typescript-eslint/parser",
  "plugins": ["@typescript-eslint", "prettier"],
  "rules": {
    "prettier/prettier": "error",
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/explicit-function-return-type": "warn",
    "react-hooks/exhaustive-deps": "warn",
    "no-console": "warn"
  }
}
```

```json
// .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2,
  "useTabs": false
}
```

## Performance Guidelines

### Python

1. **Use async/await for I/O operations**
2. **Select only needed columns from database**
3. **Use database indexes effectively**
4. **Implement caching for frequently accessed data**
5. **Avoid N+1 queries with eager loading**

### TypeScript/React

1. **Use React.memo for expensive components**
2. **Implement virtual scrolling for long lists**
3. **Lazy load routes and components**
4. **Use useMemo/useCallback for expensive computations**
5. **Optimize re-renders with proper dependencies**

## Security Guidelines

### Python

1. **Never commit secrets or credentials**
2. **Use environment variables for configuration**
3. **Validate all inputs**
4. **Use parameterized queries**
5. **Implement proper error handling**

### TypeScript/React

1. **Sanitize all user inputs**
2. **Use HTTPS for all API calls**
3. **Implement proper authentication**
4. **Validate data on client and server**
5. **Use CSP headers for XSS prevention**

## Resources and Tools

### Recommended Tools

**Python:**
- Black: Code formatting
- isort: Import sorting
- flake8: Linting
- mypy: Type checking
- bandit: Security scanning

**TypeScript:**
- ESLint: Linting
- Prettier: Formatting
- TypeScript: Type checking
- Husky: Git hooks
- lint-staged: Pre-commit hooks

### Learning Resources

- [PEP 8 Style Guide](https://pep8.org/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [React Documentation](https://react.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Clean Code](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350884/)

## Enforcement

### Automated Checks

1. **Pre-commit hooks** run on every commit
2. **CI/CD pipeline** runs on every push
3. **Code coverage** must be > 80%
4. **All tests must pass**
5. **No security vulnerabilities**

### Manual Review

1. **Code review** required for all PRs
2. **Architecture review** for major changes
3. **Security review** for sensitive changes
4. **Performance review** for optimizations

### Consequences

1. **Failed checks** block merge
2. **Repeated violations** require training
3. **Security violations** immediate action
4. **Quality issues** affect performance reviews

## Conclusion

Following these coding standards ensures:

- ✅ High-quality, maintainable code
- ✅ Consistent style across the codebase
- ✅ Fewer bugs and issues
- ✅ Easier onboarding for new developers
- ✅ Better collaboration

Remember: standards are guidelines, not rules. Use judgment and adapt when necessary, but always prioritize code clarity and maintainability.
