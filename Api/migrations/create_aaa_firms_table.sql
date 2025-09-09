-- Firms table for company/firm management
CREATE TABLE aaa_firms (
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

-- Disable RLS on firms table
ALTER TABLE aaa_firms DISABLE ROW LEVEL SECURITY;

-- Create indexes for better performance
CREATE INDEX idx_aaa_firms_company_name ON aaa_firms(company_name);
CREATE INDEX idx_aaa_firms_email ON aaa_firms(email);