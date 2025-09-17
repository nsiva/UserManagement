-- Run all MFA-related migrations

-- 1. Create email OTP table
CREATE TABLE IF NOT EXISTS aaa_email_otps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES aaa_profiles(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    otp VARCHAR(6) NOT NULL,
    purpose VARCHAR(10) NOT NULL CHECK (purpose IN ('setup', 'login')),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_aaa_email_otps_user_email ON aaa_email_otps(user_id, email);
CREATE INDEX IF NOT EXISTS idx_aaa_email_otps_otp_purpose ON aaa_email_otps(otp, purpose);
CREATE INDEX IF NOT EXISTS idx_aaa_email_otps_expires_at ON aaa_email_otps(expires_at);

-- Add constraint to prevent multiple active OTPs for same user/purpose
-- Using a partial index on just the boolean field to avoid NOW() function issues
CREATE UNIQUE INDEX IF NOT EXISTS idx_aaa_email_otps_active_unique 
ON aaa_email_otps(user_id, purpose) 
WHERE used = FALSE;

-- Disable RLS for this table
ALTER TABLE aaa_email_otps DISABLE ROW LEVEL SECURITY;

-- 2. Add mfa_method column to user profiles
ALTER TABLE aaa_profiles 
ADD COLUMN IF NOT EXISTS mfa_method VARCHAR(10) DEFAULT NULL 
CHECK (mfa_method IS NULL OR mfa_method IN ('totp', 'email'));

-- Create index for efficient lookups
CREATE INDEX IF NOT EXISTS idx_aaa_profiles_mfa_method ON aaa_profiles(mfa_method);

-- Update existing users with TOTP MFA to have 'totp' method
UPDATE aaa_profiles 
SET mfa_method = 'totp' 
WHERE mfa_secret IS NOT NULL AND mfa_method IS NULL;