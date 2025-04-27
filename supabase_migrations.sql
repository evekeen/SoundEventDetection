-- Create enum type for task status
CREATE TYPE task_status AS ENUM (
  'pending',
  'processing',
  'completed',
  'failed'
);

-- Create tasks table
CREATE TABLE tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  filename TEXT NOT NULL,
  original_filename TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  status task_status NOT NULL DEFAULT 'pending',
  impact_time_seconds FLOAT,
  error_message TEXT,
  video_url TEXT
);

-- Create indices
CREATE INDEX tasks_status_idx ON tasks (status);
CREATE INDEX tasks_created_at_idx ON tasks (created_at DESC);

-- Set up Row Level Security (RLS)
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

-- Create policies for authenticated users
CREATE POLICY "Allow full access for authenticated users" ON tasks
  FOR ALL
  TO authenticated
  USING (true);

-- Create bucket for video storage
-- Note: This needs to be done via the Supabase dashboard
-- or via the Supabase Management API, not SQL

-- Function comment
COMMENT ON TABLE tasks IS 'Stores video processing tasks for sound event detection'; 