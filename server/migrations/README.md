# Database Schema Migration

## Overview

This directory contains migration scripts to update the database schema. The main changes include:

1. Creating many-to-many relationships between plans and repos
2. Creating many-to-many relationships between user_events and plans
3. Maintaining backward compatibility during the transition

## Migration Files

- `create_many_to_many_relationships.sql`: Creates junction tables and updates existing relationships

## Schema Changes

### Before

- `plans` table had a direct foreign key to a single `repo` (1:1 relationship)
- `user_events` table had a direct foreign key to a single `plan` (N:1 relationship)

### After

- `plans` can be associated with multiple `repos` through the `plan_repos` junction table (M:N relationship)
- `user_events` can be associated with multiple `plans` through the `user_event_plans` junction table (M:N relationship)
- Original foreign key columns are kept temporarily for backward compatibility

## Migration Steps

1. Run the migration script:

```bash
psql -U your_username -d your_database -f create_many_to_many_relationships.sql
```

2. Update your application code to use the new relationships:
   - Use `plan.repos` instead of `plan.repo`
   - Use `user_event.plans` instead of `user_event.plan`

3. After all code is updated, you can remove the deprecated columns:
   - Uncomment and run the last part of the migration script

## Data Model

The new data model includes:

- `plan_repos`: Junction table linking plans to repos
  - `id`: UUID primary key
  - `plan_id`: Foreign key to plans
  - `repo_id`: Foreign key to repos

- `user_event_plans`: Junction table linking user_events to plans
  - `id`: UUID primary key
  - `user_event_id`: Foreign key to user_events
  - `plan_id`: Foreign key to plans 