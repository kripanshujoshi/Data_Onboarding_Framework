-- This is the only table you need to create for the RBAC/approval workflow

CREATE TABLE IF NOT EXISTS sql_requests (
    id SERIAL PRIMARY KEY,
    created_by VARCHAR(255) NOT NULL,
    dataset_name VARCHAR(255) NOT NULL,
    request_id UUID NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    s3_prefix TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    approved_by VARCHAR(255),
    approved_at TIMESTAMP,
    rejection_reason TEXT
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_sql_requests_status ON sql_requests(status);
CREATE INDEX IF NOT EXISTS idx_sql_requests_dataset_name ON sql_requests(dataset_name);
CREATE INDEX IF NOT EXISTS idx_sql_requests_request_id ON sql_requests(request_id);
