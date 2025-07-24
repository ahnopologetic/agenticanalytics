-- Migration: Create many-to-many relationships between plans and repos, and between user_events and plans

-- 1. Create a junction table for plans and repos
CREATE TABLE plan_repos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
    repo_id UUID NOT NULL REFERENCES repos(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (plan_id, repo_id)
);

-- 2. Migrate existing plan-repo relationships to the junction table
INSERT INTO plan_repos (plan_id, repo_id, created_at, updated_at)
SELECT id, repo_id, created_at, updated_at
FROM plans
WHERE repo_id IS NOT NULL;

-- 3. Create a junction table for user_events and plans
CREATE TABLE user_event_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_event_id UUID NOT NULL REFERENCES user_events(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_event_id, plan_id)
);

-- 4. Migrate existing user_event-plan relationships to the junction table
INSERT INTO user_event_plans (user_event_id, plan_id)
SELECT id, plan_id
FROM user_events
WHERE plan_id IS NOT NULL;

-- 5. Make the repo_id column in plans table nullable (for backward compatibility)
ALTER TABLE plans ALTER COLUMN repo_id DROP NOT NULL;

-- 6. Make the plan_id column in user_events table nullable (for backward compatibility)
ALTER TABLE user_events ALTER COLUMN plan_id DROP NOT NULL;

-- Note: The following commented statements should be executed after all code is updated
-- to use the new many-to-many relationships

-- -- Remove the repo_id column from plans table
-- ALTER TABLE plans DROP COLUMN repo_id;

-- -- Remove the plan_id column from user_events table
-- ALTER TABLE user_events DROP COLUMN plan_id; 