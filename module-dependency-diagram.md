# Module Dependency Diagram

## Helper Module Dependencies

```mermaid
graph TD
    %% Dark theme color palette with white text
    classDef ORG    fill:#0D5ED7,stroke:#444,stroke-width:4px,color:#fff
    classDef I      fill:#237046,stroke:#444,stroke-width:4px,color:#fff
    classDef P      fill:#870000,stroke:#444,stroke-width:4px,color:#fff
    classDef R      fill:#4B0082,stroke:#444,stroke-width:4px,color:#fff
    classDef O      fill:#A34700,stroke:#444,stroke-width:4px,color:#fff
    classDef C      fill:#2F4F4F,stroke:#444,stroke-width:2px,color:#fff
    classDef extra1 fill:#006C6C,stroke:#444,stroke-width:4px,color:#fff
    classDef extra2 fill:#556B2F,stroke:#444,stroke-width:4px,color:#fff
    classDef extra3 fill:#8B008B,stroke:#444,stroke-width:4px,color:#fff
    classDef extra4 fill:#696969,stroke:#444,stroke-width:4px,color:#fff

    %% Foundation Layer (ORG - Blue)
    exceptions[exceptions.py]:::ORG
    logger[logger.py]:::ORG
    path_helpers[path_helpers.py]:::ORG
    
    %% Common Utilities (I - Green)
    api_common[api_common.py]:::I
    
    %% Data Layer (P - Red)
    load_n_save[load_n_save.py]:::P
    
    %% API Implementation (O - Brown/Orange)
    rest_api_helpers[rest_api_helpers.py]:::O
    soap_api_helpers[soap_api_helpers.py]:::O
    oauth_helpers[oauth_helpers.py]:::O
    
    %% Orchestration (R - Purple)
    api_factory[api_factory.py]:::R
    config_loader[config_loader.py]:::R
    script_runner[script_runner.py]:::R
    
    %% URL Utilities (extra1 - Teal)
    url_helpers[url_helpers.py]:::extra1
    url_builders[url_builders.py]:::extra1
    
    %% Concurrency (extra2 - Olive)
    concurrency[concurrency.py]:::extra2
    
    %% User Scripts (C - Dark Gray/Teal)
    user_script[src/*.py]:::C
    
    %% Dependencies
    logger --> path_helpers
    
    api_common --> logger
    
    load_n_save --> logger
    load_n_save --> path_helpers
    load_n_save --> exceptions
    
    oauth_helpers --> logger
    oauth_helpers --> exceptions
    
    rest_api_helpers --> logger
    rest_api_helpers --> exceptions
    rest_api_helpers --> api_common
    
    soap_api_helpers --> logger
    soap_api_helpers --> exceptions
    
    url_helpers --> logger
    
    url_builders --> logger
    url_builders --> config_loader
    
    config_loader --> logger
    config_loader --> path_helpers
    config_loader --> load_n_save
    
    api_factory --> logger
    api_factory --> rest_api_helpers
    api_factory --> soap_api_helpers
    api_factory --> api_common
    
    concurrency --> logger
    concurrency --> exceptions
    
    script_runner --> logger
    script_runner --> config_loader
    script_runner --> oauth_helpers
    script_runner --> path_helpers
    script_runner --> exceptions
    
    user_script --> script_runner
    user_script --> api_factory
    user_script --> load_n_save
    user_script --> exceptions
    user_script --> logger

    %% Add legend
    subgraph Legend
        L1[Foundation - Blue]:::ORG
        L2[Common - Green]:::I
        L3[Data - Red]:::P
        L4[API - Orange]:::O
        L5[Orchestration - Purple]:::R
        L6[URL Utils - Teal]:::extra1
        L7[Concurrency - Olive]:::extra2
        L8[User Scripts - Gray]:::C
    end
```

## Helper Module Flow

```mermaid
sequenceDiagram
    participant User
    participant ScriptRunner
    participant Logger
    participant ConfigLoader
    participant OAuth

    User->>ScriptRunner: python script.py org_id env_type
    ScriptRunner->>ScriptRunner: Parse args (org_id, env_type)
    ScriptRunner->>Logger: setup_logger(org_id)
    Note over Logger: Logger now has context
    ScriptRunner->>ConfigLoader: load_config(org_id, env_type)
    ConfigLoader->>ConfigLoader: Load main config
    ConfigLoader->>ConfigLoader: Load secrets (flat)
    ConfigLoader->>ConfigLoader: Inject secrets with _prefix
    ConfigLoader-->>ScriptRunner: Return merged config
    ScriptRunner->>ScriptRunner: Inject _org_id, _env_type
    ScriptRunner->>OAuth: Get token (using _client_secret)
    ScriptRunner->>ScriptRunner: Inject _token
    ScriptRunner-->>User: Return complete config
```

## Dependency Levels

### Level 0 - No Dependencies
- **exceptions.py**: Base exception classes (no utils dependencies)

### Level 1 - Foundation
- **logger.py**: Depends on path_helpers
- **path_helpers.py**: No utils dependencies (potential circular dependency with logger needs investigation)

### Level 2 - Common Utilities
- **api_common.py**: Depends on logger

### Level 3 - Data & Authentication
- **load_n_save.py**: Depends on logger, path_helpers, exceptions
- **oauth_helpers.py**: Depends on logger, exceptions
- **config_loader.py**: Depends on logger, path_helpers, load_n_save
- **url_helpers.py**: Depends on logger

### Level 4 - API Implementation & Utilities
- **rest_api_helpers.py**: Depends on logger, exceptions, api_common
- **soap_api_helpers.py**: Depends on logger, exceptions
- **url_builders.py**: Depends on logger, config_loader
- **concurrency.py**: Depends on logger, exceptions

### Level 5 - Orchestration
- **api_factory.py**: Depends on logger, rest_api_helpers, soap_api_helpers, api_common

### Level 6 - Script Runner
- **script_runner.py**: Depends on logger, config_loader, oauth_helpers, path_helpers, exceptions

### Level 7 - User Scripts
- **src/*.py**: Typically depend on script_runner, api_factory, load_n_save, exceptions, logger

## Potential Issues Detected

### ⚠️ Circular Dependency Risk
- **logger.py** imports **path_helpers** (for get_path)
- If **path_helpers** imports **logger**, this creates a circular dependency
- **Solution**: path_helpers should not import logger, or use lazy import

## Refactoring Order

Based on dependencies, update in this order:

1. **exceptions.py** (no dependencies)
2. **path_helpers.py** (check for circular dependency first)
3. **logger.py**
4. **api_common.py**
5. **load_n_save.py**, **oauth_helpers.py**, **url_helpers.py**
6. **config_loader.py**
7. **rest_api_helpers.py**, **soap_api_helpers.py**, **concurrency.py**
8. **url_builders.py**
9. **api_factory.py**
10. **script_runner.py**

## Import Graph for Quick Reference

```python
# Foundation (no imports from utils)
exceptions.py → None

# Foundation with dependencies
path_helpers.py → (check for logger import - potential circular)
logger.py → path_helpers

# Common utilities
api_common.py → logger

# Data layer
load_n_save.py → logger, path_helpers, exceptions

# Authentication
oauth_helpers.py → logger, exceptions

# API implementations
rest_api_helpers.py → logger, exceptions, api_common
soap_api_helpers.py → logger, exceptions

# URL utilities
url_helpers.py → logger
url_builders.py → logger, config_loader

# Configuration
config_loader.py → logger, path_helpers, load_n_save

# Orchestration
api_factory.py → logger, rest_api_helpers, soap_api_helpers, api_common
concurrency.py → logger, exceptions

# Top level
script_runner.py → logger, config_loader, oauth_helpers, path_helpers, exceptions
```