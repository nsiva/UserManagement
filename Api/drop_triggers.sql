-- Script to remove the database triggers for functional roles updated_at
-- Run this if the triggers were already created in your database

-- Drop the trigger
DROP TRIGGER IF EXISTS trigger_update_functional_roles_updated_at ON aaa_functional_roles;

-- Drop the function
DROP FUNCTION IF EXISTS update_functional_roles_updated_at();

-- Verify triggers are removed
SELECT trigger_name, event_object_table 
FROM information_schema.triggers 
WHERE event_object_table = 'aaa_functional_roles';

-- Should return no rows if triggers are successfully removed