-- Create user-business unit relationship table
-- This table links users with business units for organizational structure

CREATE TABLE IF NOT EXISTS aaa_user_business_units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    business_unit_id UUID NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID, -- Optional: track who made the assignment
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    CONSTRAINT fk_aaa_user_business_units_user_id 
        FOREIGN KEY (user_id) REFERENCES aaa_profiles(id) ON DELETE CASCADE,
    CONSTRAINT fk_aaa_user_business_units_business_unit_id 
        FOREIGN KEY (business_unit_id) REFERENCES aaa_business_units(id) ON DELETE CASCADE,
    CONSTRAINT fk_aaa_user_business_units_assigned_by 
        FOREIGN KEY (assigned_by) REFERENCES aaa_profiles(id) ON DELETE SET NULL,
    
    -- Unique constraint to prevent duplicate assignments
    CONSTRAINT uk_aaa_user_business_units_user_business_unit 
        UNIQUE (user_id, business_unit_id)
);

-- Create indexes for optimal query performance
CREATE INDEX IF NOT EXISTS idx_aaa_user_business_units_user_id 
    ON aaa_user_business_units(user_id);

CREATE INDEX IF NOT EXISTS idx_aaa_user_business_units_business_unit_id 
    ON aaa_user_business_units(business_unit_id);

-- Additional composite index for common queries
CREATE INDEX IF NOT EXISTS idx_aaa_user_business_units_user_active 
    ON aaa_user_business_units(user_id, is_active);

-- Create updated_at trigger for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_aaa_user_business_units_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_aaa_user_business_units_updated_at
    BEFORE UPDATE ON aaa_user_business_units
    FOR EACH ROW
    EXECUTE FUNCTION update_aaa_user_business_units_updated_at();

-- Disable Row Level Security for direct access via service key
ALTER TABLE aaa_user_business_units DISABLE ROW LEVEL SECURITY;

-- Add helpful comments
COMMENT ON TABLE aaa_user_business_units IS 'Links users to business units for organizational structure and access control';
COMMENT ON COLUMN aaa_user_business_units.user_id IS 'Reference to user in aaa_profiles table';
COMMENT ON COLUMN aaa_user_business_units.business_unit_id IS 'Reference to business unit in aaa_business_units table';
COMMENT ON COLUMN aaa_user_business_units.assigned_by IS 'User who made this assignment (optional)';
COMMENT ON COLUMN aaa_user_business_units.is_active IS 'Whether this assignment is currently active';