-- Extend existing aaa_clients table to support OAuth PKCE flow
-- This approach reuses the existing table instead of creating a new one

-- Add OAuth-specific columns to existing aaa_clients table
ALTER TABLE aaa_clients 
ADD COLUMN IF NOT EXISTS redirect_uris TEXT[], -- Array of allowed redirect URIs for OAuth
ADD COLUMN IF NOT EXISTS client_type VARCHAR(20) DEFAULT 'client_credentials' CHECK (client_type IN ('client_credentials', 'oauth_pkce')),
ADD COLUMN IF NOT EXISTS description TEXT; -- Optional description for the client

-- Make client_secret optional (not needed for PKCE clients)
ALTER TABLE aaa_clients ALTER COLUMN client_secret DROP NOT NULL;

-- Update indexes to support new OAuth functionality
CREATE INDEX IF NOT EXISTS idx_aaa_clients_type ON aaa_clients(client_type);
CREATE INDEX IF NOT EXISTS idx_aaa_clients_active_type ON aaa_clients(is_active, client_type) WHERE is_active = TRUE;

-- Update the authorization codes table to reference the unified clients table
-- (This assumes the new table hasn't been created yet)
CREATE TABLE IF NOT EXISTS aaa_authorization_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT UNIQUE NOT NULL,
    client_id TEXT NOT NULL REFERENCES aaa_clients(client_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES aaa_profiles(id) ON DELETE CASCADE,
    redirect_uri TEXT NOT NULL,
    code_challenge TEXT NOT NULL, -- For PKCE
    code_challenge_method TEXT NOT NULL DEFAULT 'S256', -- PKCE method (S256 or plain)
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for authorization codes
CREATE INDEX IF NOT EXISTS idx_aaa_authorization_codes_code ON aaa_authorization_codes(code);
CREATE INDEX IF NOT EXISTS idx_aaa_authorization_codes_client_id ON aaa_authorization_codes(client_id);
CREATE INDEX IF NOT EXISTS idx_aaa_authorization_codes_user_id ON aaa_authorization_codes(user_id);
CREATE INDEX IF NOT EXISTS idx_aaa_authorization_codes_expires_at ON aaa_authorization_codes(expires_at);

-- Insert example OAuth PKCE client
INSERT INTO aaa_clients (client_id, name, client_type, redirect_uris, scopes, description, is_active) 
VALUES (
    'test_external_app', 
    'Test External Application',
    'oauth_pkce',
    ARRAY['http://localhost:4202/oauth/callback', 'http://localhost:3000/callback'],
    ARRAY['read:profile', 'read:roles'],
    'Test OAuth PKCE client for external application integration',
    TRUE
) ON CONFLICT (client_id) DO NOTHING;

-- Display success message
DO $$
BEGIN
    RAISE NOTICE 'aaa_clients table extended for OAuth PKCE support!';
    RAISE NOTICE 'Client types supported: client_credentials, oauth_pkce';
    RAISE NOTICE 'Test OAuth PKCE client "test_external_app" has been added.';
END $$;