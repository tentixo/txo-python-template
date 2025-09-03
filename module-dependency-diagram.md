# Module Dependency Diagram

## Architecture Overview

The TXO Python Template v2.1 follows a layered architecture with clear dependency rules. Understanding these dependencies is crucial for maintenance and refactoring.

## Dependency Layers

### Layer 1: Foundation (No Dependencies)
- `exceptions.py` - Custom exception hierarchy
- `path_helpers.py` - Path management utilities

### Layer 2: Core Services 
- `logger.py` - Depends on: path_helpers
- `api_common.py` - Depends on: logger

### Layer 3: Data & I/O
- `load_n_save.py` - Depends on: exceptions, logger, path_helpers

### Layer 4: API Implementation
- `oauth_helpers.py` - Depends on: logger, exceptions
- `rest_api_helpers.py` - Depends on: logger, exceptions, api_common
- `url_helpers.py` - Depends on: logger

### Layer 5: Orchestration
- `config_loader.py` - Depends on: logger, path_helpers, load_n_save, exceptions
- `api_factory.py` - Depends on: logger, rest_api_helpers, api_common
- `script_runner.py` - Depends on: config_loader, oauth_helpers, logger, exceptions

### Layer 6: User Scripts
- `src/*.py` - Depends on: script_runner, api_factory, load_n_save, exceptions, logger

## Visual Dependency Graph

```mermaid
graph TD
    %% Color scheme for different layers
    classDef foundation fill:#0D5ED7,stroke:#444,stroke-width:4px,color:#fff
    classDef core fill:#237046,stroke:#444,stroke-width:4px,color:#fff
    classDef data fill:#870000,stroke:#444,stroke-width:4px,color:#fff
    classDef api fill:#A34700,stroke:#444,stroke-width:4px,color:#fff
    classDef orchestration fill:#4B0082,stroke:#444,stroke-width:4px,color:#fff
    classDef user fill:#2F4F4F,stroke:#444,stroke-width:2px,color:#fff

    %% Foundation Layer (Blue)
    exceptions[exceptions.py]:::foundation
    path_helpers[path_helpers.py]:::foundation
    
    %% Core Services (Green)
    logger[logger.py]:::core
    api_common[api_common.py]:::core
    
    %% Data Layer (Red)
    load_n_save[load_n_save.py]:::data
    
    %% API Implementation (Orange)
    rest_api_helpers[rest_api_helpers.py]:::api
    oauth_helpers[oauth_helpers.py]:::api
    url_helpers[url_helpers.py]:::api
    
    %% Orchestration (Purple)
    config_loader[config_loader.py]:::orchestration
    api_factory[api_factory.py]:::orchestration
    script_runner[script_runner.py]:::orchestration
    concurrency[concurrency.py]:::orchestration
    
    %% User Scripts (Gray)
    user_script[src/*.py]:::user
    
    %% Dependencies
    logger --> path_helpers
    
    api_common --> logger
    
    load_n_save --> exceptions
    load_n_save --> logger
    load_n_save --> path_helpers
    
    oauth_helpers --> logger
    oauth_helpers --> exceptions
    
    rest_api_helpers --> logger
    rest_api_helpers --> exceptions
    rest_api_helpers --> api_common
    
    url_helpers --> logger
    
    config_loader --> logger
    config_loader --> path_helpers
    config_loader --> load_n_save
    config_loader --> exceptions
    
    api_factory --> logger
    api_factory --> rest_api_helpers
    api_factory --> api_common
    
    concurrency --> logger
    concurrency --> exceptions
    
    script_runner --> config_loader
    script_runner --> oauth_helpers
    script_runner --> logger
    script_runner --> exceptions
    
    user_script --> script_runner
    user_script --> api_factory
    user_script --> load_n_save
    user_script --> exceptions
    user_script --> logger
    user_script --> concurrency

    %% Legend
    subgraph Legend
        L1[Foundation - No deps]:::foundation
        L2[Core - Basic deps]:::core
        L3[Data - I/O ops]:::data
        L4[API - External]:::api
        L5[Orchestration]:::orchestration
        L6[User Scripts]:::user
    end
```

## Common Operation Sequences

### Script Initialization Sequence

```mermaid
sequenceDiagram
    participant User
    participant Script as src/script.py
    participant Runner as script_runner
    participant Config as config_loader
    participant OAuth as oauth_helpers
    participant Logger as logger

    User->>Script: python script.py org env
    Script->>Runner: parse_args_and_load_config()
    Runner->>Logger: setup_logger(org_id)
    Runner->>Config: load_config(org, env)
    Config->>Config: load JSON files
    Config->>Config: validate schema
    Config->>Config: inject secrets
    Config-->>Runner: config dict
    
    alt Authentication Required
        Runner->>OAuth: get_client_credentials_token()
        OAuth->>OAuth: check cache
        alt Token Cached
            OAuth-->>Runner: cached token
        else Token Expired
            OAuth->>OAuth: request new token
            OAuth-->>Runner: new token
        end
        Runner->>Config: inject _token
    end
    
    Runner-->>Script: config with _org_id, _env_type, _token
    Script->>Script: main() executes
```

### API Call with Resilience Features

```mermaid
sequenceDiagram
    participant Script as src/script.py
    participant Factory as api_factory
    participant API as rest_api_helpers
    participant RateLimiter
    participant CircuitBreaker
    participant Session
    participant External as External API

    Script->>Factory: create_rest_api(config)
    Factory->>Factory: parse config
    Factory->>RateLimiter: create if enabled
    Factory->>CircuitBreaker: create if enabled
    Factory->>API: TxoRestAPI(limiter, breaker)
    Factory-->>Script: api instance

    Script->>API: api.get(url)
    
    API->>CircuitBreaker: is_open()?
    alt Circuit Open
        CircuitBreaker-->>API: true
        API-->>Script: ApiOperationError
    else Circuit Closed
        CircuitBreaker-->>API: false
        API->>RateLimiter: wait_if_needed()
        RateLimiter->>RateLimiter: throttle
        
        API->>Session: request(url)
        Session->>External: HTTP GET
        
        alt Success (200)
            External-->>Session: response
            Session-->>API: response
            API->>CircuitBreaker: record_success()
            API-->>Script: data
        else Rate Limited (429)
            External-->>Session: 429 + Retry-After
            Session-->>API: 429 response
            API->>API: exponential backoff
            API->>Session: retry request
        else Server Error (500)
            External-->>Session: 500 error
            Session-->>API: error
            API->>CircuitBreaker: record_failure()
            API->>API: retry with backoff
        else Async Operation (202)
            External-->>Session: 202 + Location
            Session-->>API: 202 response
            loop Poll until complete
                API->>API: wait(Retry-After)
                API->>Session: GET Location
                Session->>External: check status
                External-->>Session: status
            end
            API-->>Script: final result
        end
    end
```

### File Save with Type Detection

```mermaid
sequenceDiagram
    participant Script as src/script.py
    participant DataHandler as load_n_save
    participant PathHelper as path_helpers
    participant FileSystem as File System

    Script->>DataHandler: save(data, "output", "file.json")
    DataHandler->>DataHandler: detect type from data
    
    alt DataFrame detected
        DataHandler->>DataHandler: check extension
        alt .csv extension
            DataHandler->>DataFrame: to_csv()
        else .xlsx extension
            DataHandler->>DataFrame: to_excel()
        end
    else Dict/List detected
        DataHandler->>DataHandler: DecimalEncoder
        DataHandler->>DataHandler: json.dumps()
    else String detected
        DataHandler->>DataHandler: write as text
    end
    
    DataHandler->>PathHelper: get_path("output", "file.json")
    PathHelper->>PathHelper: resolve path
    PathHelper-->>DataHandler: Path object
    
    DataHandler->>FileSystem: write file
    FileSystem-->>DataHandler: success
    DataHandler-->>Script: Path to saved file
```

## Refactoring Order

When updating the template, follow this dependency order to avoid breaking changes:

1. **Foundation** (no dependencies)
   - exceptions.py
   - path_helpers.py

2. **Core Services** (minimal dependencies)
   - logger.py (depends on path_helpers)
   - api_common.py (depends on logger)

3. **Data Layer** (foundation + core)
   - load_n_save.py

4. **API Implementation** (all previous)
   - oauth_helpers.py
   - rest_api_helpers.py
   - url_helpers.py

5. **Orchestration** (all previous)
   - config_loader.py
   - api_factory.py
   - concurrency.py
   - script_runner.py

6. **User Scripts** (everything)
   - Update last after all utilities are working

## Key Design Principles

### 1. Unidirectional Dependencies
- Lower layers never depend on higher layers
- Foundation modules have zero dependencies
- User scripts can use everything

### 2. Single Responsibility
Each module has one clear purpose:
- `logger.py` - Only logging
- `path_helpers.py` - Only path management
- `api_factory.py` - Only API creation

### 3. Dependency Injection
Configuration and dependencies are injected, not hardcoded:
```python
# Good - injected
def process(config: Dict[str, Any]):
    api = create_rest_api(config)

# Bad - hardcoded
def process():
    api = create_rest_api(load_my_config())
```

### 4. Fail Fast Philosophy
All required configuration uses hard-fail:
```python
# Good - fails immediately if missing
url = config['global']['api-url']

# Bad - silent failure
url = config.get('global', {}).get('api-url', 'default')
```

## Testing Dependencies

To test a module in isolation, you only need its dependencies:

```bash
# Test exceptions.py - no dependencies needed
python -c "from utils.exceptions import HelpfulError; raise HelpfulError('test', 'fix', 'example')"

# Test logger.py - needs path_helpers
python -c "from utils.logger import setup_logger; logger = setup_logger(); logger.info('test')"

# Test api_factory.py - needs many dependencies
# Better to use test_v2_features.py which tests everything
```

## Common Circular Dependency Issues

### Problem Areas to Avoid

1. **Config in Logger**
   - Don't make logger depend on config_loader
   - Logger should work with minimal setup

2. **API in Exceptions**
   - Exceptions shouldn't know about API details
   - Keep exceptions generic

3. **Script Runner in Helpers**
   - Helper modules shouldn't import script_runner
   - Keep helpers independent

### Signs of Circular Dependencies

- ImportError at module level
- Functions that import inside themselves
- Modules that import each other

### Resolution Strategy

1. Move shared code to a lower layer
2. Use dependency injection instead of imports
3. Create a new intermediate module
4. Use type hints with string literals for forward references

## Performance Considerations

### Import Cost
Modules are imported in order of dependency. Heavy modules are loaded lazily:

```python
# Good - lazy import
def process_excel():
    import pandas as pd  # Only loaded when needed
    
# Bad - always imported
import pandas as pd  # Loaded even if not used
```

### Singleton Patterns
Several modules use singleton patterns for efficiency:
- `logger.py` - Single logger instance
- `config_loader.py` - Cached configuration
- `api_factory.py` - Optional API instance caching

### Connection Pooling
API modules reuse connections:
- `rest_api_helpers.py` - SessionManager with LRU cache
- Maximum 50 sessions cached
- Thread-safe implementation

## Version Compatibility

### v2.1 Breaking Changes
- Config structure is nested (rate-limiting, circuit-breaker as objects)
- All config access uses hard-fail
- save_json() → save() with type detection
- MinimalRestAPI → TxoRestAPI

### Backward Compatibility
Where possible, v2.1 maintains compatibility:
- Old flat config can be migrated
- Helper functions still work
- Core patterns unchanged

## Troubleshooting

### Module Not Found
```python
ImportError: cannot import name 'X' from 'utils.Y'
```
- Check if module exists
- Verify no typos in import
- Ensure dependencies are installed

### Circular Import
```python
ImportError: cannot import name 'X' from partially initialized module
```
- Check dependency graph above
- Move shared code to lower layer
- Use lazy imports

### Type Errors
```python
TypeError: X() takes no arguments
```
- Check if using v2.1 syntax
- Verify config structure matches
- Update to new class names

## Future Architecture Considerations

### Potential Improvements
1. **Plugin System** - Dynamic helper loading
2. **Async Support** - asyncio for I/O operations
3. **Caching Layer** - Redis/memcached integration
4. **Message Queue** - For long-running operations
5. **Metrics Collection** - Performance monitoring

### Maintaining the Architecture
1. Keep dependencies unidirectional
2. Document any new modules in this diagram
3. Add tests for new dependencies
4. Update refactoring order when adding modules
5. Consider impact on all layers when changing interfaces