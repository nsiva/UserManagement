-- Organizations table for company/organization management
CREATE TABLE aaa_organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name TEXT NOT NULL,
    address_1 TEXT,
    address_2 TEXT,
    city_town TEXT,
    state TEXT,
    zip TEXT,
    country TEXT,
    email TEXT,
    phone_number TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Disable RLS on organizations table
ALTER TABLE aaa_organizations DISABLE ROW LEVEL SECURITY;

-- Create indexes for better performance
CREATE INDEX idx_aaa_organizations_company_name ON aaa_organizations(company_name);
CREATE INDEX idx_aaa_organizations_email ON aaa_organizations(email);