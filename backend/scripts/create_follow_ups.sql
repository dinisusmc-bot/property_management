SET search_path TO sales, public;

CREATE TABLE IF NOT EXISTS follow_ups (
  id SERIAL PRIMARY KEY,
  lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  activity_id INTEGER REFERENCES lead_activities(id),
  follow_up_type VARCHAR(50) NOT NULL,
  scheduled_date DATE NOT NULL,
  scheduled_time TIME,
  completed BOOLEAN DEFAULT FALSE,
  completed_at TIMESTAMP,
  completed_by INTEGER,
  outcome VARCHAR(50),
  notes TEXT,
  reminder_sent BOOLEAN DEFAULT FALSE,
  assigned_to INTEGER NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  CONSTRAINT valid_follow_up_type CHECK (follow_up_type IN ('call', 'email', 'meeting', 'quote', 'other')),
  CONSTRAINT valid_outcome CHECK (outcome IS NULL OR outcome IN ('successful', 'no_answer', 'voicemail', 'rescheduled', 'lost'))
);

CREATE INDEX IF NOT EXISTS idx_follow_ups_lead ON follow_ups(lead_id);
CREATE INDEX IF NOT EXISTS idx_follow_ups_assigned ON follow_ups(assigned_to);
CREATE INDEX IF NOT EXISTS idx_follow_ups_scheduled ON follow_ups(scheduled_date, completed) WHERE NOT completed;
CREATE INDEX IF NOT EXISTS idx_follow_ups_overdue ON follow_ups(scheduled_date) WHERE NOT completed AND scheduled_date < CURRENT_DATE;

GRANT ALL ON follow_ups TO athena;
GRANT USAGE, SELECT ON SEQUENCE follow_ups_id_seq TO athena;
