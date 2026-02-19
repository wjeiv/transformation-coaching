# Performance Specifications

**Version:** v1.0.0  
**Last Updated:** 2025-02-17  
**Author**: Performance Team  
**Review Status**: Approved

## Overview

This document defines the performance requirements, benchmarks, and optimization strategies for the Transformation Coaching platform. Performance is critical for user experience, especially given the integration with external APIs and the handling of workout data.

## Performance Objectives

### Primary Objectives

1. **Fast Initial Load**: Users should see meaningful content within 2 seconds
2. **Responsive Interactions**: All UI interactions should feel instantaneous
3. **Efficient Data Handling**: Large datasets should not degrade performance
4. **Scalable Architecture**: System should handle growth without degradation
5. **Mobile Optimization**: Excellent performance on mobile networks

### Success Metrics

| Metric | Target | Measurement Tool |
|--------|--------|------------------|
| First Contentful Paint (FCP) | < 1.5s | Lighthouse |
| Largest Contentful Paint (LCP) | < 2.5s | Lighthouse |
| First Input Delay (FID) | < 100ms | Lighthouse |
| Cumulative Layout Shift (CLS) | < 0.1 | Lighthouse |
| Time to Interactive (TTI) | < 3.8s | Lighthouse |
| API Response Time | < 500ms (95th percentile) | Server monitoring |
| Database Query Time | < 200ms (95th percentile) | Database monitoring |

## Frontend Performance

### Core Web Vitals

```typescript
// Performance monitoring implementation
class PerformanceMonitor {
  private observer: PerformanceObserver;
  
  constructor() {
    this.setupObservers();
  }
  
  private setupObservers() {
    // Largest Contentful Paint
    this.observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach((entry) => {
        if (entry.entryType === 'largest-contentful-paint') {
          this.trackMetric('LCP', entry.startTime);
        }
      });
    });
    this.observer.observe({ entryTypes: ['largest-contentful-paint'] });
    
    // First Input Delay
    const fidObserver = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        if (entry.entryType === 'first-input') {
          this.trackMetric('FID', entry.processingStart - entry.startTime);
        }
      });
    });
    fidObserver.observe({ entryTypes: ['first-input'] });
    
    // Cumulative Layout Shift
    let clsValue = 0;
    const clsObserver = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        if (!entry.hadRecentInput) {
          clsValue += entry.value;
          this.trackMetric('CLS', clsValue);
        }
      });
    });
    clsObserver.observe({ entryTypes: ['layout-shift'] });
  }
  
  private trackMetric(name: string, value: number) {
    // Send to analytics
    gtag('event', 'web_vitals', {
      name,
      value: Math.round(value),
      event_category: 'Web Vitals'
    });
  }
}

// Initialize monitoring
new PerformanceMonitor();
```

### Bundle Optimization

```javascript
// webpack.config.js optimizations
module.exports = {
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
        common: {
          name: 'common',
          minChunks: 2,
          chunks: 'all',
          enforce: true
        }
      }
    },
    runtimeChunk: {
      name: 'runtime'
    }
  },
  performance: {
    maxAssetSize: 244 * 1024, // 244KB
    maxEntrypointSize: 244 * 1024,
  }
};
```

### Code Splitting Strategy

```typescript
// Route-based code splitting
import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import LoadingSpinner from './components/LoadingSpinner';

// Lazy loaded components
const Dashboard = lazy(() => import('./pages/Dashboard'));
const CoachDashboard = lazy(() => import('./pages/CoachDashboard'));
const AthleteDashboard = lazy(() => import('./pages/AthleteDashboard'));
const Settings = lazy(() => import('./pages/Settings'));

const AppRoutes = () => {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/dashboard/coach" element={<CoachDashboard />} />
        <Route path="/dashboard/athlete" element={<AthleteDashboard />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Suspense>
  );
};
```

### Image Optimization

```typescript
// Responsive image component
interface OptimizedImageProps {
  src: string;
  alt: string;
  width: number;
  height: number;
  priority?: boolean;
}

const OptimizedImage: React.FC<OptimizedImageProps> = ({
  src,
  alt,
  width,
  height,
  priority = false
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState(false);
  
  return (
    <div className="relative overflow-hidden">
      {!isLoaded && !error && (
        <div className="absolute inset-0 bg-gray-200 animate-pulse" />
      )}
      
      <picture>
        <source
          srcSet={`${src}?format=webp&w=${width}&h=${height}`}
          type="image/webp"
        />
        <img
          src={`${src}?w=${width}&h=${height}`}
          alt={alt}
          width={width}
          height={height}
          loading={priority ? 'eager' : 'lazy'}
          onLoad={() => setIsLoaded(true)}
          onError={() => setError(true)}
          className={`transition-opacity duration-300 ${
            isLoaded ? 'opacity-100' : 'opacity-0'
          }`}
        />
      </picture>
      
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
          <span className="text-gray-500">Failed to load image</span>
        </div>
      )}
    </div>
  );
};
```

### Virtual Scrolling for Large Lists

```typescript
// Virtualized workout list
import { FixedSizeList as List } from 'react-window';
import { useMemo } from 'react';

interface VirtualizedWorkoutListProps {
  workouts: Workout[];
  height: number;
}

const VirtualizedWorkoutList: React.FC<VirtualizedWorkoutListProps> = ({
  workouts,
  height
}) => {
  const Row = useMemo(() => ({ index, style }: { index: number; style: any }) => (
    <div style={style}>
      <WorkoutCard workout={workouts[index]} />
    </div>
  ), [workouts]);
  
  return (
    <List
      height={height}
      itemCount={workouts.length}
      itemSize={120}
      itemData={workouts}
    >
      {Row}
    </List>
  );
};
```

## Backend Performance

### Database Optimization

```sql
-- Database configuration for performance
-- postgresql.conf settings

-- Memory settings
shared_buffers = 256MB                  -- 25% of RAM
effective_cache_size = 1GB              -- 75% of RAM
work_mem = 4MB                          -- Per operation
maintenance_work_mem = 64MB

-- Connection settings
max_connections = 100
shared_preload_libraries = 'pg_stat_statements'

-- Query optimization
random_page_cost = 1.1                  -- For SSD
effective_io_concurrency = 200          -- For SSD

-- Logging for monitoring
log_min_duration_statement = 1000       -- Log slow queries
log_checkpoints = on
log_connections = on
log_disconnections = on
```

```python
# Database query optimization
from sqlalchemy import select, Index, text
from sqlalchemy.orm import selectinload

class WorkoutRepository:
    async def get_workouts_with_pagination(
        self,
        db: AsyncSession,
        page: int,
        size: int,
        user_id: str
    ) -> List[Workout]:
        """Optimized pagination with index usage"""
        offset = (page - 1) * size
        
        query = (
            select(Workout)
            .where(Workout.user_id == user_id)
            .order_by(Workout.created_at.desc())
            .offset(offset)
            .limit(size)
            .options(selectinload(Workout.steps))  # Eager load
        )
        
        result = await db.execute(query)
        return result.scalars().unique().all()
    
    async def search_workouts(
        self,
        db: AsyncSession,
        user_id: str,
        search_term: str
    ) -> List[Workout]:
        """Full-text search with proper indexing"""
        # Using PostgreSQL full-text search
        query = text("""
            SELECT w.* FROM workouts w
            WHERE w.user_id = :user_id
            AND to_tsvector('english', w.name || ' ' || w.description)
                @@ plainto_tsquery('english', :search_term)
            ORDER BY ts_rank(
                to_tsvector('english', w.name || ' ' || w.description),
                plainto_tsquery('english', :search_term)
            ) DESC
        """)
        
        result = await db.execute(
            query,
            {"user_id": user_id, "search_term": search_term}
        )
        return result.scalars().all()

# Database indexes for performance
indexes = [
    Index('idx_workouts_user_created', Workout.user_id, Workout.created_at.desc()),
    Index('idx_workouts_search', Workout.name, Workout.description),
    Index('idx_shared_workouts_athlete_date', SharedWorkout.athlete_id, SharedWorkout.created_at.desc()),
]
```

### API Response Optimization

```python
# FastAPI performance optimizations
from fastapi import FastAPI, Depends, Response
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
import gzip
import json

app = FastAPI()

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Response caching decorator
from functools import wraps
import time

def cache_response(expire: int = 300):
    def decorator(func):
        cache = {}
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            key = str(args) + str(sorted(kwargs.items()))
            now = time.time()
            
            # Check cache
            if key in cache:
                data, timestamp = cache[key]
                if now - timestamp < expire:
                    return data
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            cache[key] = (result, now)
            
            return result
        return wrapper
    return decorator

# Optimized endpoint
@app.get("/api/v1/coach/workouts")
@cache_response(expire=60)  # Cache for 1 minute
async def get_workouts(
    current_user: User = Depends(get_current_user),
    page: int = 1,
    size: int = 20
):
    """Get workouts with pagination and caching"""
    workouts = await workout_service.get_workouts_with_pagination(
        db, page, size, current_user.id
    )
    
    # Use Pydantic for fast serialization
    return {
        "workouts": [WorkoutResponse.from_orm(w) for w in workouts],
        "total": await workout_service.count_workouts(current_user.id),
        "page": page,
        "size": size
    }

# Streaming response for large datasets
@app.get("/api/v1/coach/workouts/export")
async def export_workouts(
    current_user: User = Depends(get_current_user),
    format: str = "csv"
):
    """Stream workout data to avoid memory issues"""
    
    async def generate_csv():
        # Write header
        yield "name,date,duration,distance\n"
        
        # Stream data
        async for workout in workout_service.stream_workouts(current_user.id):
            row = f"{workout.name},{workout.date},{workout.duration},{workout.distance}\n"
            yield row
    
    return StreamingResponse(
        generate_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=workouts.csv"}
    )
```

### Async Operations and Concurrency

```python
# Concurrent API calls
import asyncio
import httpx
from typing import List

class GarminService:
    async def fetch_multiple_workout_types(
        self,
        user_id: str,
        start_date: date,
        end_date: date
    ) -> dict:
        """Fetch different workout types concurrently"""
        
        async with httpx.AsyncClient() as client:
            tasks = [
                self.fetch_workouts(client, user_id, start_date, end_date, "running"),
                self.fetch_workouts(client, user_id, start_date, end_date, "cycling"),
                self.fetch_workouts(client, user_id, start_date, end_date, "swimming"),
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            return {
                "running": results[0] if not isinstance(results[0], Exception) else [],
                "cycling": results[1] if not isinstance(results[1], Exception) else [],
                "swimming": results[2] if not isinstance(results[2], Exception) else [],
            }
    
    async def sync_workouts_batch(
        self,
        user_id: str,
        workout_ids: List[str]
    ) -> List[dict]:
        """Process workouts in batches to avoid rate limits"""
        
        BATCH_SIZE = 10
        results = []
        
        for i in range(0, len(workout_ids), BATCH_SIZE):
            batch = workout_ids[i:i + BATCH_SIZE]
            
            # Process batch concurrently
            tasks = [self.process_workout(wid) for wid in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            results.extend(batch_results)
            
            # Rate limiting delay
            if i + BATCH_SIZE < len(workout_ids):
                await asyncio.sleep(1)
        
        return results
```

## Caching Strategy

### Multi-Level Caching

```python
# Redis caching implementation
import redis
import json
from typing import Optional, Any

class CacheManager:
    def __init__(self):
        self.redis = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cached data"""
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> None:
        """Set cached data with optional expiration"""
        data = json.dumps(value, default=str)
        await self.redis.set(key, data, ex=expire)
    
    async def delete(self, key: str) -> None:
        """Delete cached data"""
        await self.redis.delete(key)
    
    async def invalidate_pattern(self, pattern: str) -> None:
        """Delete keys matching pattern"""
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

# Cache decorator
def cache_result(key_prefix: str, expire: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            cached = await cache_manager.get(cache_key)
            if cached is not None:
                return cached
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache_manager.set(cache_key, result, expire)
            
            return result
        return wrapper
    return decorator

# Usage
@cache_result(key_prefix="user_workouts", expire=600)
async def get_user_workouts(user_id: str, page: int, size: int):
    return await workout_service.get_workouts(user_id, page, size)
```

### Frontend Caching

```typescript
// React Query for server state management
import { QueryClient, QueryClientProvider, useQuery } from 'react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: 3,
      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
  },
});

// Custom hook with caching
export const useWorkouts = (page: number, size: number) => {
  return useQuery(
    ['workouts', page, size],
    () => api.getWorkouts(page, size),
    {
      keepPreviousData: true, // Keep previous data while fetching new
      staleTime: 2 * 60 * 1000, // 2 minutes
    }
  );
};

// Prefetching for better UX
const WorkoutList: React.FC = () => {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useWorkouts(page, 20);
  const queryClient = useQueryClient();
  
  // Prefetch next page
  useEffect(() => {
    if (data?.hasMore) {
      queryClient.prefetchQuery(
        ['workouts', page + 1, 20],
        () => api.getWorkouts(page + 1, 20)
      );
    }
  }, [data, page, queryClient]);
  
  return (
    // Component JSX
  );
};
```

## Monitoring and Analytics

### Performance Monitoring Setup

```python
# Performance monitoring middleware
import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class PerformanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # Log slow requests
        if process_time > 1.0:  # Log if > 1 second
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {process_time:.2f}s"
            )
        
        # Add performance headers
        response.headers["X-Process-Time"] = str(process_time)
        
        # Send to monitoring
        metrics.histogram(
            'http_request_duration_seconds',
            process_time,
            tags={
                'method': request.method,
                'path': request.url.path,
                'status_code': response.status_code
            }
        )
        
        return response

# Add middleware to app
app.add_middleware(PerformanceMiddleware)
```

### Real User Monitoring (RUM)

```typescript
// RUM implementation
class RealUserMonitoring {
  private metrics: Map<string, number[]> = new Map();
  
  constructor() {
    this.setupNavigationTiming();
    this.setupResourceTiming();
    this.setupUserInteractions();
  }
  
  private setupNavigationTiming() {
    window.addEventListener('load', () => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      
      this.recordMetric('dns', navigation.domainLookupEnd - navigation.domainLookupStart);
      this.recordMetric('tcp', navigation.connectEnd - navigation.connectStart);
      this.recordMetric('request', navigation.responseStart - navigation.requestStart);
      this.recordMetric('response', navigation.responseEnd - navigation.responseStart);
      this.recordMetric('dom', navigation.domContentLoadedEventStart - navigation.responseEnd);
      this.recordMetric('load', navigation.loadEventStart - navigation.domContentLoadedEventStart);
      
      this.sendMetrics();
    });
  }
  
  private setupResourceTiming() {
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        if (entry.entryType === 'resource') {
          const resource = entry as PerformanceResourceTiming;
          this.recordMetric(`resource_${resource.name}`, resource.duration);
        }
      });
    });
    
    observer.observe({ entryTypes: ['resource'] });
  }
  
  private setupUserInteractions() {
    ['click', 'keydown', 'touchstart'].forEach(eventType => {
      document.addEventListener(eventType, (event) => {
        const start = performance.now();
        
        // Use requestAnimationFrame to measure interaction delay
        requestAnimationFrame(() => {
          const delay = performance.now() - start;
          this.recordMetric(`interaction_${eventType}`, delay);
        });
      }, { passive: true });
    });
  }
  
  private recordMetric(name: string, value: number) {
    if (!this.metrics.has(name)) {
      this.metrics.set(name, []);
    }
    this.metrics.get(name)!.push(value);
  }
  
  private sendMetrics() {
    const aggregated = this.aggregateMetrics();
    
    // Send to analytics
    fetch('/api/v1/analytics/performance', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(aggregated)
    }).catch(console.error);
  }
  
  private aggregateMetrics() {
    const result: Record<string, any> = {};
    
    this.metrics.forEach((values, name) => {
      const sorted = values.sort((a, b) => a - b);
      result[name] = {
        count: values.length,
        min: sorted[0],
        max: sorted[sorted.length - 1],
        avg: values.reduce((a, b) => a + b, 0) / values.length,
        p50: sorted[Math.floor(sorted.length * 0.5)],
        p95: sorted[Math.floor(sorted.length * 0.95)],
        p99: sorted[Math.floor(sorted.length * 0.99)]
      };
    });
    
    return result;
  }
}

// Initialize RUM
new RealUserMonitoring();
```

## Performance Budgets

### Resource Budgets

```typescript
// Performance budget configuration
const PERFORMANCE_BUDGETS = {
  // JavaScript bundles
  javascript: {
    main: 244 * 1024,      // 244KB
    vendor: 300 * 1024,     // 300KB
    total: 500 * 1024       // 500KB total
  },
  
  // CSS
  stylesheets: {
    main: 50 * 1024,        // 50KB
    total: 100 * 1024       // 100KB total
  },
  
  // Images
  images: {
    hero: 500 * 1024,       // 500KB for hero images
    thumbnail: 50 * 1024,    // 50KB for thumbnails
    total: 2 * 1024 * 1024  // 2MB total per page
  },
  
  // Fonts
  fonts: {
    total: 250 * 1024       // 250KB total
  },
  
  // API responses
  api: {
    initial: 100 * 1024,     // 100KB for initial data
    incremental: 50 * 1024   // 50KB for incremental loads
  }
};

// Budget validation with webpack-bundle-analyzer
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;

module.exports = {
  plugins: [
    new BundleAnalyzerPlugin({
      analyzerMode: 'static',
      openAnalyzer: false,
      reportFilename: '../reports/bundle-report.html'
    })
  ]
};
```

### Performance Testing with Lighthouse CI

```yaml
# .lighthouserc.js
module.exports = {
  ci: {
    collect: {
      url: [
        'http://localhost:3000',
        'http://localhost:3000/login',
        'http://localhost:3000/dashboard'
      ],
      numberOfRuns: 3,
      settings: {
        chromeFlags: '--no-sandbox --headless'
      }
    },
    assert: {
      assertions: {
        'categories:performance': ['warn', { minScore: 0.8 }],
        'categories:accessibility': ['error', { minScore: 0.9 }],
        'categories:best-practices': ['warn', { minScore: 0.8 }],
        'categories:seo': ['warn', { minScore: 0.8 }],
        'categories:pwa': 'off'
      }
    },
    upload: {
      target: 'temporary-public-storage'
    }
  }
};
```

## Optimization Strategies

### Lazy Loading Implementation

```typescript
// Intersection Observer for lazy loading
const useLazyLoad = (threshold = 0.1) => {
  const [isIntersecting, setIsIntersecting] = useState(false);
  const [hasLoaded, setHasLoaded] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasLoaded) {
          setIsIntersecting(true);
          setHasLoaded(true);
        }
      },
      { threshold }
    );
    
    if (ref.current) {
      observer.observe(ref.current);
    }
    
    return () => observer.disconnect();
  }, [threshold, hasLoaded]);
  
  return { ref, isIntersecting };
};

// Lazy image component
const LazyImage: React.FC<ImageProps> = ({ src, alt, ...props }) => {
  const { ref, isIntersecting } = useLazyLoad();
  const [imageSrc, setImageSrc] = useState<string>();
  
  useEffect(() => {
    if (isIntersecting && !imageSrc) {
      setImageSrc(src);
    }
  }, [isIntersecting, src, imageSrc]);
  
  return (
    <div ref={ref} {...props}>
      {imageSrc ? (
        <img src={imageSrc} alt={alt} />
      ) : (
        <div className="animate-pulse bg-gray-200 h-full w-full" />
      )}
    </div>
  );
};
```

### Service Worker for Caching

```typescript
// service-worker.ts
const CACHE_NAME = 'tc-app-v1';
const STATIC_ASSETS = [
  '/',
  '/static/js/main.js',
  '/static/css/main.css',
  '/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(STATIC_ASSETS))
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  
  // API requests - network first, cache fallback
  if (request.url.includes('/api/')) {
    event.respondWith(
      fetch(request)
        .then(response => {
          // Cache successful responses
          if (response.ok) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME)
              .then(cache => cache.put(request, responseClone));
          }
          return response;
        })
        .catch(() => {
          // Try cache if network fails
          return caches.match(request);
        })
    );
    return;
  }
  
  // Static assets - cache first, network fallback
  event.respondWith(
    caches.match(request)
      .then(response => {
        if (response) {
          return response;
        }
        
        return fetch(request)
          .then(response => {
            // Cache new static assets
            if (request.destination === 'script' || 
                request.destination === 'style' ||
                request.destination === 'image') {
              const responseClone = response.clone();
              caches.open(CACHE_NAME)
                .then(cache => cache.put(request, responseClone));
            }
            return response;
          });
      })
  );
});
```

### Database Query Optimization

```python
# Query optimization examples
from sqlalchemy import text, Index
from sqlalchemy.orm import joinedload, selectinload

# 1. Use indexes effectively
class Workout(Base):
    __tablename__ = 'workouts'
    
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, nullable=False)
    sport_type = Column(String, nullable=False)
    
    # Composite index for common queries
    __table_args__ = (
        Index('idx_workouts_user_sport_date', 'user_id', 'sport_type', 'created_at.desc'),
    )

# 2. Optimize queries with proper joins
def get_user_workouts_with_stats(db: AsyncSession, user_id: str):
    """Single query instead of N+1"""
    query = (
        select(Workout, WorkoutStats)
        .join(WorkoutStats, Workout.id == WorkoutStats.workout_id)
        .where(Workout.user_id == user_id)
        .options(selectinload(Workout.steps))
        .order_by(Workout.created_at.desc())
    )
    
    return await db.execute(query)

# 3. Use window functions for pagination
async def get_paginated_workouts(
    db: AsyncSession,
    user_id: str,
    page: int,
    size: int
):
    """Efficient pagination with window functions"""
    offset = (page - 1) * size
    
    query = text("""
        SELECT * FROM (
            SELECT 
                w.*,
                COUNT(*) OVER() as total_count,
                ROW_NUMBER() OVER(ORDER BY w.created_at DESC) as row_num
            FROM workouts w
            WHERE w.user_id = :user_id
        ) ranked
        WHERE row_num BETWEEN :offset + 1 AND :offset + :size
    """)
    
    result = await db.execute(
        query,
        {"user_id": user_id, "offset": offset, "size": size}
    )
    
    return result.fetchall()
```

## Performance Testing

### Load Testing with k6

```javascript
// performance-tests/load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export let options = {
  stages: [
    { duration: '2m', target: 10 },   // Ramp up
    { duration: '5m', target: 10 },   // Stay at 10
    { duration: '2m', target: 50 },   // Ramp up to 50
    { duration: '5m', target: 50 },   // Stay at 50
    { duration: '2m', target: 100 },  // Ramp up to 100
    { duration: '5m', target: 100 },  // Stay at 100
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
    errors: ['rate<0.01'],
  },
};

const BASE_URL = 'http://localhost:8000';

export default function() {
  // Test authentication endpoint
  const loginResponse = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
    email: 'test@example.com',
    password: 'password123'
  }), {
    headers: { 'Content-Type': 'application/json' }
  });
  
  const token = loginResponse.json('access_token');
  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };
  
  // Test workout endpoint
  const workoutsResponse = http.get(`${BASE_URL}/api/v1/coach/workouts`, { headers });
  
  check(workoutsResponse, {
    'workouts status is 200': (r) => r.status === 200,
    'workouts response time < 500ms': (r) => r.timings.duration < 500,
  }) || errorRate.add(1);
  
  sleep(1);
}
```

### Frontend Performance Testing

```typescript
// performance-tests/component-performance.test.ts
import { render, screen } from '@testing-library/react';
import { PerformanceObserver } from 'perf_hooks';
import { WorkoutList } from '../components/WorkoutList';

describe('Component Performance', () => {
  it('should render 1000 items within performance budget', async () => {
    const workouts = Array.from({ length: 1000 }, (_, i) => ({
      id: `workout-${i}`,
      name: `Workout ${i}`,
      duration: 1800,
      distance: 5000
    }));
    
    // Measure render time
    const start = performance.now();
    
    render(<WorkoutList workouts={workouts} />);
    
    const renderTime = performance.now() - start;
    
    // Assert performance budget
    expect(renderTime).toBeLessThan(100); // 100ms budget
    expect(screen.getAllByTestId('workout-item')).toHaveLength(1000);
  });
  
  it('should not cause layout shifts', () => {
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        if (entry.entryType === 'layout-shift') {
          expect(entry.value).toBeLessThan(0.1);
        }
      });
    });
    
    observer.observe({ entryTypes: ['layout-shift'] });
    
    render(<WorkoutList workouts={testWorkouts} />);
  });
});
```

## Continuous Performance Monitoring

### Performance Dashboard

```typescript
// Performance dashboard component
const PerformanceDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>();
  
  useEffect(() => {
    const fetchMetrics = async () => {
      const response = await fetch('/api/v1/admin/performance');
      const data = await response.json();
      setMetrics(data);
    };
    
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 60000); // Update every minute
    
    return () => clearInterval(interval);
  }, []);
  
  if (!metrics) return <LoadingSpinner />;
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <MetricCard
        title="Avg Response Time"
        value={`${metrics.avgResponseTime}ms`}
        trend={metrics.responseTimeTrend}
      />
      <MetricCard
        title="95th Percentile"
        value={`${metrics.p95ResponseTime}ms`}
        trend={metrics.p95Trend}
      />
      <MetricCard
        title="Error Rate"
        value={`${(metrics.errorRate * 100).toFixed(2)}%`}
        trend={metrics.errorRateTrend}
      />
      <MetricCard
        title="Active Users"
        value={metrics.activeUsers}
        trend={metrics.activeUsersTrend}
      />
    </div>
  );
};
```

### Alerting Configuration

```yaml
# alerts/performance-alerts.yml
groups:
  - name: performance
    rules:
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"
      
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"
      
      - alert: DatabaseSlowQuery
        expr: avg_over_time(db_query_duration_seconds[5m]) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database queries are slow"
          description: "Average query time is {{ $value }}s"
```

## Performance Optimization Checklist

### Frontend Optimization

- [ ] Bundle size analysis and reduction
- [ ] Code splitting implementation
- [ ] Image optimization and lazy loading
- [ ] Service worker for caching
- [ ] Remove unused dependencies
- [ ] Implement virtual scrolling for long lists
- [ ] Optimize re-renders with React.memo
- [ ] Use Web Workers for heavy computations

### Backend Optimization

- [ ] Database query optimization
- [ ] Implement proper indexing
- [ ] Add response caching
- [ ] Use connection pooling
- [ ] Implement rate limiting
- [ ] Add compression middleware
- [ ] Optimize async operations
- [ ] Monitor and optimize memory usage

### Infrastructure Optimization

- [ ] CDN implementation
- [ ] Load balancer configuration
- [ ] Auto-scaling policies
- [ ] Database read replicas
- [ ] Redis caching layer
- [ ] Monitor resource utilization
- [ ] Optimize container sizes
- [ ] Implement health checks

## Future Performance Considerations

### Advanced Optimizations

1. **Edge Computing**: Deploy to edge locations for lower latency
2. **GraphQL**: Reduce over-fetching with selective queries
3. **WebAssembly**: For performance-critical computations
4. HTTP/3: QUIC protocol for better performance
5. **Predictive Prefetching**: AI-driven content prefetching

### Monitoring Enhancements

1. **Real User Monitoring (RUM)**: Detailed user experience tracking
2. **Synthetic Monitoring**: Automated performance testing
3. **Distributed Tracing**: End-to-end request tracking
4. **Anomaly Detection**: ML-based performance issue detection
5. **Performance Budget Enforcement**: Automated CI/CD checks
