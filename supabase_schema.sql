-- Supabase database schema for NJ Health Facility Enforcement Actions Monitor
-- Run this SQL in your Supabase SQL editor to create the necessary tables

-- Create the main enforcement_actions table
CREATE TABLE IF NOT EXISTS enforcement_actions (
    id TEXT PRIMARY KEY,
    scraped_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    facility_name TEXT NOT NULL,
    facility_address TEXT,
    facility_license_number TEXT,
    enforcement_date DATE,
    enforcement_action_type TEXT,
    penalty_amount TEXT,
    violation_summary TEXT,
    key_violations JSONB DEFAULT '[]'::jsonb,
    effective_date TEXT,
    contact_information TEXT,
    pdf_url TEXT,
    severity_level TEXT CHECK (severity_level IN ('LOW', 'MEDIUM', 'HIGH')) DEFAULT 'LOW',
    priority_score INTEGER DEFAULT 0 CHECK (priority_score >= 0 AND priority_score <= 100),
    raw_web_data JSONB DEFAULT '{}'::jsonb,
    raw_pdf_data JSONB DEFAULT '{}'::jsonb,
    validation JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_enforcement_actions_facility_name ON enforcement_actions(facility_name);
CREATE INDEX IF NOT EXISTS idx_enforcement_actions_enforcement_date ON enforcement_actions(enforcement_date);
CREATE INDEX IF NOT EXISTS idx_enforcement_actions_severity_level ON enforcement_actions(severity_level);
CREATE INDEX IF NOT EXISTS idx_enforcement_actions_priority_score ON enforcement_actions(priority_score);
CREATE INDEX IF NOT EXISTS idx_enforcement_actions_scraped_at ON enforcement_actions(scraped_at);
CREATE INDEX IF NOT EXISTS idx_enforcement_actions_action_type ON enforcement_actions(enforcement_action_type);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_enforcement_actions_updated_at 
    BEFORE UPDATE ON enforcement_actions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create a view for high priority entries
CREATE OR REPLACE VIEW high_priority_actions AS
SELECT 
    id,
    facility_name,
    enforcement_action_type,
    enforcement_date,
    penalty_amount,
    severity_level,
    priority_score,
    violation_summary,
    created_at
FROM enforcement_actions
WHERE severity_level = 'HIGH' OR priority_score >= 70
ORDER BY priority_score DESC, enforcement_date DESC;

-- Create a view for recent entries (last 30 days)
CREATE OR REPLACE VIEW recent_actions AS
SELECT 
    id,
    facility_name,
    enforcement_action_type,
    enforcement_date,
    penalty_amount,
    severity_level,
    priority_score,
    created_at
FROM enforcement_actions
WHERE enforcement_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY enforcement_date DESC;

-- Create a statistics view
CREATE OR REPLACE VIEW enforcement_statistics AS
SELECT 
    COUNT(*) as total_entries,
    COUNT(CASE WHEN enforcement_date >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as entries_last_7_days,
    COUNT(CASE WHEN enforcement_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as entries_last_30_days,
    COUNT(CASE WHEN severity_level = 'HIGH' THEN 1 END) as high_severity_count,
    COUNT(CASE WHEN severity_level = 'MEDIUM' THEN 1 END) as medium_severity_count,
    COUNT(CASE WHEN severity_level = 'LOW' THEN 1 END) as low_severity_count,
    AVG(priority_score) as avg_priority_score,
    MAX(enforcement_date) as latest_enforcement_date,
    MIN(enforcement_date) as earliest_enforcement_date
FROM enforcement_actions;

-- Create a table for monitoring logs
CREATE TABLE IF NOT EXISTS monitoring_logs (
    id SERIAL PRIMARY KEY,
    log_level TEXT NOT NULL CHECK (log_level IN ('INFO', 'WARNING', 'ERROR', 'DEBUG')),
    message TEXT NOT NULL,
    facility_name TEXT,
    entry_id TEXT,
    error_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for monitoring logs
CREATE INDEX IF NOT EXISTS idx_monitoring_logs_created_at ON monitoring_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_monitoring_logs_log_level ON monitoring_logs(log_level);

-- Create a table for email notifications sent
CREATE TABLE IF NOT EXISTS email_notifications (
    id SERIAL PRIMARY KEY,
    entry_ids TEXT[] NOT NULL,
    email_subject TEXT NOT NULL,
    email_content TEXT,
    recipient_email TEXT NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT
);

-- Create index for email notifications
CREATE INDEX IF NOT EXISTS idx_email_notifications_sent_at ON email_notifications(sent_at);
CREATE INDEX IF NOT EXISTS idx_email_notifications_success ON email_notifications(success);

-- Grant necessary permissions (adjust as needed for your setup)
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO your_service_role;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO your_service_role;
