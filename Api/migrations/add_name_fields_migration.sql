-- Migration script to add name fields to existing aaa_profiles table
-- Run this in Supabase SQL Editor if you have existing data

-- Add the new name columns to existing table
ALTER TABLE aaa_profiles 
ADD COLUMN IF NOT EXISTS first_name TEXT,
ADD COLUMN IF NOT EXISTS middle_name TEXT, 
ADD COLUMN IF NOT EXISTS last_name TEXT;

-- Update the updated_at timestamp
UPDATE aaa_profiles SET updated_at = NOW() WHERE first_name IS NULL;

-- Verify the migration
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'aaa_profiles' 
AND table_schema = 'public'
ORDER BY ordinal_position;

-- Sample query to verify the structure
SELECT id, email, first_name, middle_name, last_name, is_admin, created_at
FROM aaa_profiles 
LIMIT 5;