# Backend Testing Guide

**Version:** v1.0.0  
**Last Updated:** 2025-02-17  
**Author**: Backend Team  
**Review Status**: Approved

## Overview

This document provides comprehensive guidelines for testing the FastAPI backend of the Transformation Coaching platform. It covers unit tests, integration tests, API testing, database testing, and performance testing.

## Testing Architecture

### Test Structure

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Test configuration and fixtures
│   ├── unit/                    # Unit tests
│   │   ├── test_services/
│   │   ├── test_utils/
│   │   └── test_models/
│   ├── integration/             # Integration tests
│   │   ├── test_api/
│   │   ├── test_database/
│   │   └── test_external/
│   ├── e2e/                     # End-to-end tests
│   └── performance/             # Performance tests
├── pytest.ini                  # pytest configuration
└── requirements-test.txt        # Test dependencies
```

## Test Configuration

### pytest.ini

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --cov=app
    --cov-report=html
    --cov-report=xml
    --cov-report=term-missing
    --cov-fail-under=80
    --strict-markers
    --disable-warnings
    -v
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
    external: Tests requiring external services
    garmin: Garmin integration tests
```

### conftest.py

```python
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db"

# Test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=True,
)

# Test session
TestSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def setup_database():
    """Create test database tables."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session(setup_database):
    """Create a test database session."""
    async with TestSessionLocal() as session:
        yield session

@pytest_asyncio.fixture
async def client(db_session):
    """Create a test client with database override."""
    app.dependency_overrides[get_db] = lambda: db_session
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User"
    }

@pytest.fixture
async def test_user(db_session, test_user_data):
    """Create a test user in the database."""
    from app.models.user import User
    from app.core.security import get_password_hash
    
    user = User(
        email=test_user_data["email"],
        hashed_password=get_password_hash(test_user_data["password"]),
        full_name=test_user_data["full_name"],
        role="athlete",
        is_active=True,
        is_verified=True
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user

@pytest.fixture
async def auth_headers(client, test_user_data):
    """Get authentication headers for a test user."""
    response = await client.post("/api/v1/auth/login", json=test_user_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def mock_garmin_client(mocker):
    """Mock Garmin client for testing."""
    mock = mocker.patch("app.services.garmin.GarminConnect")
    mock.return_value.login = AsyncMock()
    mock.return_value.get_workouts = AsyncMock(return_value=[])
    return mock
```

## Unit Testing

### Service Layer Testing

```python
# tests/unit/test_services/test_user_service.py
import pytest
from unittest.mock import AsyncMock, patch

from app.services.user import UserService
from app.models.user import User, UserRole

class TestUserService:
    @pytest.fixture
    def user_service(self, db_session):
        return UserService(db_session)
    
    async def test_create_user_success(self, user_service, test_user_data):
        # Act
        user = await user_service.create_user(test_user_data)
        
        # Assert
        assert user.email == test_user_data["email"]
        assert user.full_name == test_user_data["full_name"]
        assert user.role == UserRole.ATHLETE
        assert user.is_active is True
        assert user.is_verified is False
    
    async def test_create_user_duplicate_email(self, user_service, test_user, test_user_data):
        # Act & Assert
        with pytest.raises(ValueError, match="Email already registered"):
            await user_service.create_user(test_user_data)
    
    async def test_update_user_success(self, user_service, test_user):
        # Arrange
        update_data = {"full_name": "Updated Name"}
        
        # Act
        updated_user = await user_service.update_user(test_user.id, update_data)
        
        # Assert
        assert updated_user.full_name == "Updated Name"
    
    async def test_update_user_not_found(self, user_service):
        # Act & Assert
        with pytest.raises(ValueError, match="User not found"):
            await user_service.update_user(999, {"full_name": "Test"})
```

### Utility Function Testing

```python
# tests/unit/test_utils/test_security.py
import pytest
from datetime import datetime, timedelta

from app.core.security import (
    create_access_token,
    verify_token,
    get_password_hash,
    verify_password
)

class TestSecurity:
    def test_password_hashing(self):
        password = "TestPass123!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("WrongPass", hashed)
    
    def test_jwt_token_creation(self):
        data = {"sub": "123"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_jwt_token_verification(self):
        data = {"sub": "123", "exp": datetime.utcnow() + timedelta(minutes=15)}
        token = create_access_token(data)
        
        payload = verify_token(token)
        assert payload["sub"] == "123"
    
    def test_jwt_token_expired(self):
        data = {"sub": "123", "exp": datetime.utcnow() - timedelta(minutes=1)}
        token = create_access_token(data)
        
        with pytest.raises(Exception, match="Token has expired"):
            verify_token(token)
```

### Model Testing

```python
# tests/unit/test_models/test_user.py
import pytest
from datetime import datetime

from app.models.user import User, UserRole

class TestUserModel:
    def test_user_creation(self):
        user = User(
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
            role=UserRole.COACH
        )
        
        assert user.email == "test@example.com"
        assert user.role == UserRole.COACH
        assert user.is_active is True  # Default value
        assert user.is_verified is False  # Default value
    
    def test_user_repr(self):
        user = User(email="test@example.com")
        assert repr(user) == "<User test@example.com>"
    
    def test_user_role_validation(self):
        with pytest.raises(ValueError):
            User(email="test@example.com", role="invalid_role")
```

## Integration Testing

### API Endpoint Testing

```python
# tests/integration/test_api/test_auth.py
import pytest
from httpx import AsyncClient

class TestAuthAPI:
    async def test_register_success(self, client: AsyncClient, test_user_data):
        # Act
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert "id" in data
        assert "password" not in data
    
    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        # Act
        response = await client.post("/api/v1/auth/register", json={
            "email": test_user.email,
            "password": "AnotherPass123!",
            "full_name": "Another User"
        })
        
        # Assert
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    async def test_login_success(self, client: AsyncClient, test_user_data):
        # First register
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Then login
        response = await client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_login_invalid_credentials(self, client: AsyncClient):
        response = await client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "WrongPass"
        })
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    async def test_protected_endpoint_without_token(self, client: AsyncClient):
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    async def test_protected_endpoint_with_token(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "full_name" in data
```

### Database Testing

```python
# tests/integration/test_database/test_user_repository.py
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.user import User, UserRole
from app.repositories.user import UserRepository

class TestUserRepository:
    @pytest.fixture
    def repository(self, db_session):
        return UserRepository(db_session)
    
    async def test_create_user(self, repository, test_user_data):
        user = User(
            email=test_user_data["email"],
            hashed_password="hashed",
            full_name=test_user_data["full_name"],
            role=UserRole.ATHLETE
        )
        
        created_user = await repository.create(user)
        assert created_user.id is not None
        
        # Verify in database
        retrieved = await repository.get_by_id(created_user.id)
        assert retrieved.email == user.email
    
    async def test_get_by_email(self, repository, test_user):
        user = await repository.get_by_email(test_user.email)
        assert user is not None
        assert user.id == test_user.id
    
    async def test_unique_email_constraint(self, repository, test_user):
        with pytest.raises(IntegrityError):
            duplicate = User(
                email=test_user.email,
                hashed_password="hashed",
                full_name="Duplicate",
                role=UserRole.ATHLETE
            )
            await repository.create(duplicate)
    
    async def test_soft_delete(self, repository, test_user):
        await repository.soft_delete(test_user.id)
        
        deleted_user = await repository.get_by_id(test_user.id)
        assert deleted_user.is_active is False
```

### External API Testing

```python
# tests/integration/test_external/test_garmin_service.py
import pytest
from unittest.mock import AsyncMock, patch

from app.services.garmin import GarminService

class TestGarminService:
    @pytest.mark.external
    async def test_real_garmin_connection(self):
        """Test with real Garmin credentials - only run manually."""
        # This test should be run manually with real credentials
        pass
    
    async def test_garmin_sync_success(self, mock_garmin_client):
        service = GarminService("encrypted_credentials")
        
        workouts = await service.sync_workouts(
            start_date="2024-01-01",
            end_date="2024-01-31"
        )
        
        assert isinstance(workouts, list)
        mock_garmin_client.return_value.get_workouts.assert_called_once()
    
    async def test_garmin_sync_failure(self, mock_garmin_client):
        mock_garmin_client.return_value.get_workouts.side_effect = Exception("API Error")
        
        service = GarminService("encrypted_credentials")
        
        with pytest.raises(Exception, match="API Error"):
            await service.sync_workouts("2024-01-01", "2024-01-31")
```

## End-to-End Testing

### Complete User Workflows

```python
# tests/e2e/test_user_workflows.py
import pytest
from httpx import AsyncClient

class TestUserWorkflows:
    async def test_complete_user_registration_flow(self, client: AsyncClient):
        # Step 1: Register
        user_data = {
            "email": "workflow@example.com",
            "password": "WorkflowPass123!",
            "full_name": "Workflow User"
        }
        
        response = await client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        
        # Step 2: Login
        response = await client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        assert response.status_code == 200
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 3: Get profile
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["email"] == user_data["email"]
        
        # Step 4: Update profile
        response = await client.put("/api/v1/auth/me", headers=headers, json={
            "full_name": "Updated Name"
        })
        assert response.status_code == 200
        assert response.json()["full_name"] == "Updated Name"
    
    async def test_coach_athlete_workflow(self, client: AsyncClient):
        # Create coach
        coach_data = {
            "email": "coach@example.com",
            "password": "CoachPass123!",
            "full_name": "Test Coach"
        }
        await client.post("/api/v1/auth/register", json=coach_data)
        
        coach_response = await client.post("/api/v1/auth/login", json={
            "email": coach_data["email"],
            "password": coach_data["password"]
        })
        coach_token = coach_response.json()["access_token"]
        coach_headers = {"Authorization": f"Bearer {coach_token}"}
        
        # Create athlete
        athlete_data = {
            "email": "athlete@example.com",
            "password": "AthletePass123!",
            "full_name": "Test Athlete"
        }
        await client.post("/api/v1/auth/register", json=athlete_data)
        
        # Admin promotes coach and links athlete (simplified)
        # In real test, you'd need admin credentials
        
        # Test coach can view athletes
        response = await client.get("/api/v1/coach/athletes", headers=coach_headers)
        assert response.status_code == 200
```

## Performance Testing

### Load Testing with k6

```javascript
// tests/performance/api_load_test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export let options = {
  stages: [
    { duration: '2m', target: 10 }, // Ramp up to 10 users
    { duration: '5m', target: 10 }, // Stay at 10 users
    { duration: '2m', target: 50 }, // Ramp up to 50 users
    { duration: '5m', target: 50 }, // Stay at 50 users
    { duration: '2m', target: 0 },  // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    errors: ['rate<0.1'],             // Error rate below 10%
  },
};

const BASE_URL = 'http://localhost:8000';

export function setup() {
  // Setup - create test user and get token
  const loginResponse = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
    email: 'test@example.com',
    password: 'TestPass123!'
  }), {
    headers: { 'Content-Type': 'application/json' }
  });
  
  return {
    token: loginResponse.json('access_token')
  };
}

export default function(data) {
  const headers = {
    'Authorization': `Bearer ${data.token}`,
    'Content-Type': 'application/json'
  };
  
  // Test API endpoints
  let responses = {
    profile: http.get(`${BASE_URL}/api/v1/auth/me`, { headers }),
    workouts: http.get(`${BASE_URL}/api/v1/coach/workouts`, { headers }),
  };
  
  // Check responses
  check(responses.profile, {
    'profile status is 200': (r) => r.status === 200,
    'profile response time < 500ms': (r) => r.timings.duration < 500,
  }) || errorRate.add(1);
  
  check(responses.workouts, {
    'workouts status is 200': (r) => r.status === 200,
    'workouts response time < 500ms': (r) => r.timings.duration < 500,
  }) || errorRate.add(1);
  
  sleep(1);
}
```

### Database Performance Testing

```python
# tests/performance/test_database_performance.py
import pytest
import time
from sqlalchemy import text

from app.models.user import User

class TestDatabasePerformance:
    async def test_bulk_user_creation_performance(self, db_session):
        """Test creating 1000 users efficiently."""
        start_time = time.time()
        
        users = []
        for i in range(1000):
            user = User(
                email=f"user{i}@example.com",
                hashed_password="hashed",
                full_name=f"User {i}",
                role="athlete"
            )
            users.append(user)
        
        db_session.add_all(users)
        await db_session.commit()
        
        duration = time.time() - start_time
        
        # Should complete within 5 seconds
        assert duration < 5.0, f"Bulk insert took {duration} seconds"
    
    async def test_query_performance_with_index(self, db_session):
        """Test query performance with proper indexing."""
        # Create test data
        for i in range(10000):
            user = User(
                email=f"user{i}@example.com",
                hashed_password="hashed",
                full_name=f"User {i}",
                role="athlete" if i % 2 == 0 else "coach"
            )
            db_session.add(user)
        await db_session.commit()
        
        # Test indexed query
        start_time = time.time()
        result = await db_session.execute(
            text("SELECT * FROM users WHERE role = 'athlete'")
        )
        athletes = result.fetchall()
        duration = time.time() - start_time
        
        assert len(athletes) == 5000
        assert duration < 0.5, f"Query took {duration} seconds"
```

## Test Data Management

### Factories for Test Data

```python
# tests/factories.py
import factory
from factory.alchemy import SQLAlchemyModelFactory

from app.models.user import User, UserRole
from app.core.database import async_session

class BaseFactory(SQLAlchemyModelFactory):
    class Meta:
        sqlalchemy_session = async_session
        sqlalchemy_session_persistence = "commit"

class UserFactory(BaseFactory):
    class Meta:
        model = User
    
    email = factory.Faker('email')
    full_name = factory.Faker('name')
    hashed_password = factory.PostGenerationMethodCall(
        'set_password', 'TestPass123!'
    )
    role = factory.Iterator([UserRole.ATHLETE, UserRole.COACH])
    is_active = True
    is_verified = True

class CoachFactory(UserFactory):
    role = UserRole.COACH
    full_name = factory.Faker('name')
    bio = factory.Faker('paragraph')
    certifications = factory.List([
        factory.Faker('sentence')
    ])

class AthleteFactory(UserFactory):
    role = UserRole.ATHLETE
    date_of_birth = factory.Faker('date_of_birth')
    emergency_contact_name = factory.Faker('name')
    emergency_contact_phone = factory.Faker('phone_number')
```

### Test Data Fixtures

```python
# tests/fixtures/test_data.py
import pytest
from datetime import date, timedelta

from tests.factories import UserFactory, CoachFactory, AthleteFactory

@pytest.fixture
async def sample_coach(db_session):
    """Create a sample coach with athletes."""
    coach = await CoachFactory.create()
    
    # Create athletes for this coach
    athletes = await AthleteFactory.create_batch(5)
    
    # Link athletes to coach
    for athlete in athletes:
        relation = CoachAthleteRelation(
            coach_id=coach.id,
            athlete_id=athlete.id,
            status='active'
        )
        db_session.add(relation)
    
    await db_session.commit()
    
    return {
        "coach": coach,
        "athletes": athletes
    }

@pytest.fixture
async def workout_data():
    """Sample workout data for testing."""
    return {
        "name": "Morning Run",
        "description": "Easy 5km run",
        "sport_type": "running",
        "duration": 1800,  # 30 minutes
        "distance": 5000,  # 5km
        "steps": [
            {
                "type": "warmup",
                "duration": 300,
                "description": "Easy jogging"
            },
            {
                "type": "main",
                "duration": 1200,
                "description": "Steady pace"
            },
            {
                "type": "cooldown",
                "duration": 300,
                "description": "Easy jogging"
            }
        ]
    }
```

## Mocking and Test Doubles

### API Mocking

```python
# tests/conftest.py (continued)
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_email_service(mocker):
    """Mock email service for testing."""
    mock = mocker.patch('app.services.email.EmailService')
    mock.return_value.send_welcome_email = AsyncMock()
    mock.return_value.send_password_reset = AsyncMock()
    return mock

@pytest.fixture
def mock_garmin_api(mocker):
    """Mock Garmin API responses."""
    mock_workout = {
        "workoutId": "12345",
        "workoutName": "Test Workout",
        "sportType": {"sportTypeId": 1, "sportTypeKey": "running"},
        "duration": 1800,
        "distance": 5000
    }
    
    mock = mocker.patch('app.services.garmin.GarminConnect')
    mock.return_value.login = AsyncMock()
    mock.return_value.get_workouts = AsyncMock(return_value=[mock_workout])
    mock.return_value.get_workout = AsyncMock(return_value=mock_workout)
    mock.return_value.upload_workout = AsyncMock(return_value={"workoutId": "67890"})
    
    return mock
```

## Test Execution

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_services/test_user_service.py

# Run by marker
pytest -m unit
pytest -m integration
pytest -m "not slow"

# Run with coverage
pytest --cov=app --cov-report=html

# Run performance tests
pytest tests/performance/

# Run external API tests (requires real credentials)
pytest -m external --garmin-email=your@email.com --garmin-password=yourpass
```

### Parallel Test Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto

# Run with specific number of workers
pytest -n 4
```

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/backend-tests.yml
name: Backend Tests

on:
  push:
    branches: [ main, develop ]
    paths: [ 'backend/**' ]
  pull_request:
    branches: [ main ]
    paths: [ 'backend/**' ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_USER: testuser
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run linting
      run: |
        cd backend
        flake8 app tests
        black --check app tests
        isort --check-only app tests
    
    - name: Run security checks
      run: |
        cd backend
        bandit -r app
        safety check
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql+asyncpg://testuser:testpass@localhost:5432/testdb
        SECRET_KEY: test-secret-key
        GARMIN_ENCRYPTION_KEY: test-encryption-key
      run: |
        cd backend
        pytest --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: backend/coverage.xml
```

## Best Practices

### Test Design Principles

1. **AAA Pattern**: Arrange, Act, Assert
2. **Single Assertion**: One assertion per test when possible
3. **Descriptive Names**: Test names should describe the scenario
4. **Independent Tests**: Tests should not depend on each other
5. **Test Data Isolation**: Each test should use its own data

### Example of Well-Structured Test

```python
class TestUserService:
    async def test_create_user_with_valid_data_should_return_user_with_id(self, user_service):
        # Arrange
        user_data = {
            "email": "valid@example.com",
            "password": "ValidPass123!",
            "full_name": "Valid User"
        }
        
        # Act
        result = await user_service.create_user(user_data)
        
        # Assert
        assert result is not None
        assert result.id is not None
        assert result.email == user_data["email"]
        assert result.full_name == user_data["full_name"]
        assert result.role == UserRole.ATHLETE
        assert result.is_active is True
        assert result.is_verified is False
```

### Error Handling in Tests

```python
async def test_create_user_with_duplicate_email_should_raise_value_error(self, user_service, test_user):
    # Arrange
    duplicate_data = {
        "email": test_user.email,  # Same email as existing user
        "password": "AnotherPass123!",
        "full_name": "Another User"
    }
    
    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        await user_service.create_user(duplicate_data)
    
    assert "already registered" in str(exc_info.value)
```

## Debugging Tests

### Common Debugging Techniques

```python
# 1. Print statements (for quick debugging)
async def test_debug_example(user_service):
    user_data = {"email": "test@example.com", "password": "Pass123!", "full_name": "Test"}
    print(f"Creating user with data: {user_data}")
    user = await user_service.create_user(user_data)
    print(f"Created user: {user}")

# 2. Using pytest's -s flag to see prints
pytest -s tests/unit/test_services/test_user_service.py::TestUserService::test_debug_example

# 3. Using pdb for debugging
import pdb

async def test_with_pdb(user_service):
    pdb.set_trace()  # Execution will pause here
    user = await user_service.create_user({...})

# 4. Pytest fixtures with debugging
@pytest.fixture
def debug_db_session(db_session):
    """Debug version of db_session that doesn't rollback."""
    yield db_session
    # Don't rollback for debugging
```

### Test Logging

```python
# Configure logging for tests
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_with_logging(user_service):
    logger.debug("Starting test")
    user = await user_service.create_user(test_data)
    logger.debug(f"Created user: {user.id}")
```

## Troubleshooting

### Common Issues and Solutions

1. **Async Test Issues**
   ```python
   # Wrong: Not using async/await
   def test_async_function():
       result = async_function()  # Returns coroutine
   
   # Correct: Using async/await
   async def test_async_function():
       result = await async_function()
   ```

2. **Database Session Issues**
   ```python
   # Wrong: Using same session across tests
   db_session = TestSessionLocal()
   
   # Correct: Using fixture for fresh session
   @pytest.fixture
   async def db_session():
       async with TestSessionLocal() as session:
           yield session
   ```

3. **Mock Not Applied**
   ```python
   # Wrong: Mocking after import
   from app.services import garmin
   mock_garmin = patch('app.services.garmin.GarminConnect')
   
   # Correct: Mocking before use
   @patch('app.services.garmin.GarminConnect')
   async def test_garmin_service(mock_garmin):
       service = GarminService()
   ```

## Test Metrics and Reporting

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# View the report
open htmlcov/index.html
```

### Test Performance Metrics

```python
# Add timing to tests
import time

@pytest.fixture
def timer():
    start = time.time()
    yield
    duration = time.time() - start
    print(f"Test took {duration:.2f} seconds")
```

### Allure Reports

```bash
# Install allure-pytest
pip install allure-pytest

# Run tests with allure
pytest --alluredir=allure-results

# Generate report
allure serve allure-results
```
