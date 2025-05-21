-- Metadata Onboarding Requests table for tracking approval workflows
CREATE TABLE IF NOT EXISTS metadata_onboarding_requests (
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

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_metadata_onboarding_requests_status ON metadata_onboarding_requests(status);
CREATE INDEX IF NOT EXISTS idx_metadata_onboarding_requests_dataset_name ON metadata_onboarding_requests(dataset_name);
CREATE INDEX IF NOT EXISTS idx_metadata_onboarding_requests_request_id ON metadata_onboarding_requests(request_id);

-- Ensure we have a schema for landing tables if not already exists
CREATE SCHEMA IF NOT EXISTS landing;

-- Ensure we have a schema for staging tables if not already exists
CREATE SCHEMA IF NOT EXISTS staging;
