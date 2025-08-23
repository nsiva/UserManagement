-- User profiles table (main user data with authentication)
  CREATE TABLE aaa_profiles (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      email TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      first_name TEXT,
      middle_name TEXT,
      last_name TEXT,
      is_admin BOOLEAN DEFAULT FALSE NOT NULL,
      mfa_secret TEXT,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );

  -- Roles definition table
  CREATE TABLE aaa_roles (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      name TEXT UNIQUE NOT NULL,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );

  -- User-Role junction table (many-to-many relationship)
  CREATE TABLE aaa_user_roles (
      user_id UUID NOT NULL REFERENCES aaa_profiles(id) ON DELETE CASCADE,
      role_id UUID NOT NULL REFERENCES aaa_roles(id) ON DELETE CASCADE,
      assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      PRIMARY KEY (user_id, role_id)
  );

  -- API clients for client credentials flow
  CREATE TABLE aaa_clients (
      client_id TEXT PRIMARY KEY,
      client_secret TEXT NOT NULL,
      name TEXT, -- Optional: human-readable client name
      scopes TEXT[], -- Optional: array of allowed scopes
      is_active BOOLEAN DEFAULT TRUE NOT NULL,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
  );

  -- Disable RLS on all new tables
  ALTER TABLE aaa_profiles DISABLE ROW LEVEL SECURITY;
  ALTER TABLE aaa_roles DISABLE ROW LEVEL SECURITY;
  ALTER TABLE aaa_user_roles DISABLE ROW LEVEL SECURITY;
  ALTER TABLE aaa_clients DISABLE ROW LEVEL SECURITY;

  -- Create indexes for better performance
  CREATE INDEX idx_aaa_profiles_email ON aaa_profiles(email);
  CREATE INDEX idx_aaa_user_roles_user_id ON aaa_user_roles(user_id);
  CREATE INDEX idx_aaa_user_roles_role_id ON aaa_user_roles(role_id);
  CREATE INDEX idx_aaa_clients_active ON aaa_clients(is_active) WHERE is_active = TRUE;


    INSERT INTO aaa_roles (name) VALUES
      ('group_admin'),
      ('firm_admin'),
      ('super_user'),
      ('user');

      INSERT INTO aaa_roles (name) VALUES
      ('admin');


--TODO why scope field
INSERT INTO aaa_clients (client_id, client_secret, name, scopes) VALUES
      ('my_test_client_id', 'my_test_client_secret', 'My Test Application', ARRAY['read:users', 'manage:users']);