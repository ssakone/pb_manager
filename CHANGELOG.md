# Changelog

All notable changes to this project will be documented in this file.

## v0.1 - 2025-11-24

- Initial public version of **PocketBase Manager**.
- PocketBase instance management dashboard with:
  - Create/start/stop/restart/delete instances via PM2.
  - Version selection from GitHub releases.
  - Custom domain support for instances.
  - File manager (list/upload/download/delete/move/copy) per instance.
  - Admin user management per instance.
  - Dev mode toggle and logs viewer.
- Authentication system with styled login page.
- Footer with MIT license and author attribution.
- Automatic SQLite migration for new `domain` column.
