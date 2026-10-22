
CREATE TABLE IF NOT EXISTS hcps (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    specialty VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS interactions (
    id SERIAL PRIMARY KEY,
    hcp_id INTEGER REFERENCES hcps(id),
    interaction_type VARCHAR(50),
    interaction_date TIMESTAMP,
    attendees TEXT,
    topics_discussed TEXT,
    materials_shared TEXT,
    samples_distributed TEXT,
    sentiment VARCHAR(20),
    outcomes TEXT,
    followup_actions TEXT,
    created_via VARCHAR(20) DEFAULT 'form',
    created_at TIMESTAMP DEFAULT NOW()
);

-- A couple of seed HCPs to test against
INSERT INTO hcps (name, specialty) VALUES
    ('Dr. Smith', 'Oncology'),
    ('Dr. Sharma', 'Cardiology')
ON CONFLICT DO NOTHING;
