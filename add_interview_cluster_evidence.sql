-- Interview cluster evidence table
CREATE TABLE IF NOT EXISTS interview_cluster_evidence (
	id BIGSERIAL PRIMARY KEY,
	client_id VARCHAR(100) NOT NULL,
	cluster_id INTEGER NOT NULL,
	response_id VARCHAR(120) NOT NULL,
	evidence_label VARCHAR(20) CHECK (evidence_label IN ('FEATURED','SUPPORTING','EXCLUDE')),
	notes TEXT,
	rank INTEGER,
	created_at TIMESTAMPTZ DEFAULT NOW(),
	updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Prevent duplicate evidence entries per client/cluster/response
DO $$
BEGIN
	IF NOT EXISTS (
		SELECT 1 FROM pg_constraint WHERE conname = 'uniq_ice_client_cluster_response'
	) THEN
		ALTER TABLE interview_cluster_evidence
			ADD CONSTRAINT uniq_ice_client_cluster_response UNIQUE (client_id, cluster_id, response_id);
	END IF;
END$$;

-- Optional FK to stage1_data_responses (ignore if column/table missing)
DO $$
BEGIN
	IF EXISTS (
		SELECT 1 FROM information_schema.tables WHERE table_name = 'stage1_data_responses'
	) AND NOT EXISTS (
		SELECT 1 FROM pg_constraint WHERE conname = 'fk_ice_response_id'
	) THEN
		ALTER TABLE interview_cluster_evidence
			ADD CONSTRAINT fk_ice_response_id
			FOREIGN KEY (response_id)
			REFERENCES stage1_data_responses(response_id)
			ON DELETE CASCADE;
	END IF;
END$$;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_ice_client_cluster ON interview_cluster_evidence(client_id, cluster_id);
CREATE INDEX IF NOT EXISTS idx_ice_response_id ON interview_cluster_evidence(response_id);

-- Trigger to keep updated_at fresh
CREATE OR REPLACE FUNCTION set_updated_at_ice()
RETURNS TRIGGER AS $$
BEGIN
	NEW.updated_at = NOW();
	RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
	IF NOT EXISTS (
		SELECT 1 FROM pg_trigger WHERE tgname = 'trg_ice_updated_at'
	) THEN
		CREATE TRIGGER trg_ice_updated_at
		BEFORE UPDATE ON interview_cluster_evidence
		FOR EACH ROW EXECUTE FUNCTION set_updated_at_ice();
	END IF;
END$$; 