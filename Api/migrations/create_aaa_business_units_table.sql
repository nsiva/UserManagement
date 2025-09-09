-- Business Units table for organizational structure management
-- This table supports hierarchical business unit organization with full audit trail

CREATE TABLE aaa_business_units (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Basic information
    name TEXT NOT NULL,
    description TEXT,
    code TEXT, -- Internal reference code for business unit
    
    -- Organizational relationships
    organization_id UUID NOT NULL,
    parent_unit_id UUID, -- Self-referencing for hierarchy (optional)
    manager_id UUID, -- References user who manages this unit (optional)
    
    -- Location information
    location TEXT,
    country TEXT,
    region TEXT,
    
    -- Contact information
    email TEXT,
    phone_number TEXT,
    
    -- Audit trail
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID, -- User ID who created this record
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by UUID, -- User ID who last updated this record
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    
    -- Foreign key constraints
    CONSTRAINT fk_business_unit_organization 
        FOREIGN KEY (organization_id) REFERENCES aaa_organizations(id) ON DELETE CASCADE,
    CONSTRAINT fk_business_unit_parent 
        FOREIGN KEY (parent_unit_id) REFERENCES aaa_business_units(id) ON DELETE SET NULL,
    CONSTRAINT fk_business_unit_manager 
        FOREIGN KEY (manager_id) REFERENCES aaa_profiles(id) ON DELETE SET NULL,
    CONSTRAINT fk_business_unit_created_by 
        FOREIGN KEY (created_by) REFERENCES aaa_profiles(id) ON DELETE SET NULL,
    CONSTRAINT fk_business_unit_updated_by 
        FOREIGN KEY (updated_by) REFERENCES aaa_profiles(id) ON DELETE SET NULL,
    
    -- Business logic constraints
    CONSTRAINT chk_business_unit_not_self_parent 
        CHECK (parent_unit_id != id), -- Prevent self-referencing
    CONSTRAINT chk_business_unit_name_length 
        CHECK (LENGTH(TRIM(name)) >= 2), -- Minimum name length
    CONSTRAINT chk_business_unit_code_format 
        CHECK (code IS NULL OR (LENGTH(TRIM(code)) >= 2 AND code ~ '^[A-Z0-9_-]+$')), -- Alphanumeric code format
    CONSTRAINT chk_business_unit_email_format 
        CHECK (email IS NULL OR email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$') -- Valid email format
);

-- Disable RLS on business units table for direct API access
ALTER TABLE aaa_business_units DISABLE ROW LEVEL SECURITY;

-- Create indexes for better performance
CREATE INDEX idx_aaa_business_units_organization_id ON aaa_business_units(organization_id);
CREATE INDEX idx_aaa_business_units_parent_unit_id ON aaa_business_units(parent_unit_id);
CREATE INDEX idx_aaa_business_units_manager_id ON aaa_business_units(manager_id);
CREATE INDEX idx_aaa_business_units_name ON aaa_business_units(name);
CREATE INDEX idx_aaa_business_units_code ON aaa_business_units(code) WHERE code IS NOT NULL;
CREATE INDEX idx_aaa_business_units_is_active ON aaa_business_units(is_active);
CREATE INDEX idx_aaa_business_units_created_at ON aaa_business_units(created_at);

-- Create unique constraint on code within organization (if code is provided)
CREATE UNIQUE INDEX idx_aaa_business_units_unique_code_per_org 
    ON aaa_business_units(organization_id, code) 
    WHERE code IS NOT NULL;

-- Create unique constraint on name within organization for same parent
CREATE UNIQUE INDEX idx_aaa_business_units_unique_name_per_parent 
    ON aaa_business_units(organization_id, COALESCE(parent_unit_id, '00000000-0000-0000-0000-000000000000'), name);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_aaa_business_units_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at timestamp
CREATE TRIGGER trigger_update_aaa_business_units_updated_at
    BEFORE UPDATE ON aaa_business_units
    FOR EACH ROW
    EXECUTE FUNCTION update_aaa_business_units_updated_at();

-- Function to prevent circular hierarchy
CREATE OR REPLACE FUNCTION check_business_unit_hierarchy()
RETURNS TRIGGER AS $$
BEGIN
    -- Only check if parent_unit_id is being set
    IF NEW.parent_unit_id IS NOT NULL THEN
        -- Check if the new parent would create a circular reference
        WITH RECURSIVE hierarchy_check AS (
            -- Start with the proposed parent
            SELECT parent_unit_id, 1 as level
            FROM aaa_business_units 
            WHERE id = NEW.parent_unit_id
            
            UNION ALL
            
            -- Follow the hierarchy up
            SELECT bu.parent_unit_id, hc.level + 1
            FROM aaa_business_units bu
            JOIN hierarchy_check hc ON bu.id = hc.parent_unit_id
            WHERE hc.level < 10 -- Prevent infinite recursion
        )
        SELECT 1 FROM hierarchy_check 
        WHERE parent_unit_id = NEW.id
        LIMIT 1;
        
        -- If we found the current record in its own ancestry, it's circular
        IF FOUND THEN
            RAISE EXCEPTION 'Cannot create circular hierarchy: Business unit cannot be an ancestor of itself';
        END IF;
        
        -- Also check that parent belongs to same organization
        IF EXISTS (
            SELECT 1 FROM aaa_business_units 
            WHERE id = NEW.parent_unit_id 
            AND organization_id != NEW.organization_id
        ) THEN
            RAISE EXCEPTION 'Parent business unit must belong to the same organization';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to enforce hierarchy constraints
CREATE TRIGGER trigger_check_business_unit_hierarchy
    BEFORE INSERT OR UPDATE ON aaa_business_units
    FOR EACH ROW
    EXECUTE FUNCTION check_business_unit_hierarchy();

-- Add helpful comments
COMMENT ON TABLE aaa_business_units IS 'Business units within organizations supporting hierarchical structure';
COMMENT ON COLUMN aaa_business_units.id IS 'Unique identifier for the business unit';
COMMENT ON COLUMN aaa_business_units.name IS 'Business unit name (required, min 2 chars)';
COMMENT ON COLUMN aaa_business_units.description IS 'Optional description of the business unit';
COMMENT ON COLUMN aaa_business_units.code IS 'Optional internal reference code (alphanumeric, unique per organization)';
COMMENT ON COLUMN aaa_business_units.organization_id IS 'Organization this business unit belongs to (required)';
COMMENT ON COLUMN aaa_business_units.parent_unit_id IS 'Parent business unit for hierarchical structure (optional)';
COMMENT ON COLUMN aaa_business_units.manager_id IS 'User who manages this business unit (optional)';
COMMENT ON COLUMN aaa_business_units.location IS 'Physical location or address';
COMMENT ON COLUMN aaa_business_units.country IS 'Country where business unit operates';
COMMENT ON COLUMN aaa_business_units.region IS 'Region or territory';
COMMENT ON COLUMN aaa_business_units.email IS 'Contact email for business unit';
COMMENT ON COLUMN aaa_business_units.phone_number IS 'Contact phone number';
COMMENT ON COLUMN aaa_business_units.created_at IS 'Timestamp when record was created';
COMMENT ON COLUMN aaa_business_units.created_by IS 'User who created this record';
COMMENT ON COLUMN aaa_business_units.updated_at IS 'Timestamp when record was last updated';
COMMENT ON COLUMN aaa_business_units.updated_by IS 'User who last updated this record';
COMMENT ON COLUMN aaa_business_units.is_active IS 'Whether the business unit is active/enabled';