-- Add mfa_method column to track user's preferred MFA method
ALTER TABLE aaa_profiles 
ADD COLUMN IF NOT EXISTS mfa_method VARCHAR(10) DEFAULT NULL 
CHECK (mfa_method IS NULL OR mfa_method IN ('totp', 'email'));

-- Create index for efficient lookups
CREATE INDEX IF NOT EXISTS idx_aaa_profiles_mfa_method ON aaa_profiles(mfa_method);

-- Update existing users with TOTP MFA to have 'totp' method
UPDATE aaa_profiles 
SET mfa_method = 'totp' 
WHERE mfa_secret IS NOT NULL AND mfa_method IS NULL;