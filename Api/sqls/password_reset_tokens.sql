-- Password reset tokens table for forgot password functionality
CREATE TABLE aaa_password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES aaa_profiles(id) ON DELETE CASCADE,
    token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Disable RLS for direct access
ALTER TABLE aaa_password_reset_tokens DISABLE ROW LEVEL SECURITY;

-- Create indexes for better performance
CREATE INDEX idx_password_reset_tokens_token ON aaa_password_reset_tokens(token);
CREATE INDEX idx_password_reset_tokens_user_id ON aaa_password_reset_tokens(user_id);
CREATE INDEX idx_password_reset_tokens_expires_at ON aaa_password_reset_tokens(expires_at);
CREATE INDEX idx_password_reset_tokens_used ON aaa_password_reset_tokens(used) WHERE used = FALSE;