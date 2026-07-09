# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0-rc5] - 2026-07-09

### Fixed

- Updated `get_me` to call the current `whoami` Hasura action instead of the removed `meHook` field.
- Fixed `set_password` to return the `updatePasswordAndEmail` action response.
- Updated `register_file` to post to the current `/task_upload_file_webhook` route.

### Changed

- Documented the `file.write` scope needed by `register_file` when using scoped API tokens.

## [0.3.0-rc1] - 2026-06-01

### Changed

- Updated the GraphQL client to use gql 4.0.0
- Updated createAPIToken syntax
- Updated Authorization header to always use Bearer with new Mythic APITokens
- Only for Mythic v4.0.0+

## [0.2.10] - 2025-10-10

### Changed

- Updated auth failures to bail out faster
- Removed command-specific checks in payload creation since they live in the server

## [0.2.9] - 2025-10-08

### Changed

- Updated one more piece of GraphQL to hardcode SSL to false for aiohttp

## [0.2.7] - 2025-08-19

### Changed

- pinning the version of gql in the setup.py to 3.5.3 since 4.0 has breaking changes for now

## [0.2.6]- 2025-05-30

### Changed

- Updated the issue_task functionality to allow supplying `payload_type` name
  - This will enable features like `forge` where the backing payload type container differs from the type of the callback
