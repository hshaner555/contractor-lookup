CREATE DATABASE IF NOT EXISTS contractors;
USE contractors;

CREATE TABLE IF NOT EXISTS contractors (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    business_name VARCHAR(255),
    normalized_business_name VARCHAR(255),
    person_name VARCHAR(255),
    normalized_person_name VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_contractors_business (normalized_business_name),
    INDEX idx_contractors_person (normalized_person_name)
);

CREATE TABLE IF NOT EXISTS credentials (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    contractor_id BIGINT NOT NULL,
    credential_number VARCHAR(255),
    credential_type VARCHAR(255) NOT NULL,
    credential_kind ENUM('LICENSE', 'REGISTRATION', 'RECORD') NOT NULL,
    issuing_authority VARCHAR(255) NOT NULL,
    jurisdiction VARCHAR(255),
    status VARCHAR(100),
    expiration_date DATE,
    source_url TEXT,
    source_record_number VARCHAR(255),
    last_verified DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_credentials_contractor FOREIGN KEY (contractor_id)
        REFERENCES contractors(id) ON DELETE CASCADE,
    UNIQUE KEY uq_credential_authority_number (issuing_authority, credential_number),
    INDEX idx_credentials_type (credential_type),
    INDEX idx_credentials_authority (issuing_authority)
);

CREATE TABLE IF NOT EXISTS import_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    source_name VARCHAR(255) NOT NULL,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP NULL,
    rows_seen INT NOT NULL DEFAULT 0,
    rows_inserted INT NOT NULL DEFAULT 0,
    rows_updated INT NOT NULL DEFAULT 0,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS review_queue (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    incoming_json JSON NOT NULL,
    candidate_contractor_id BIGINT,
    reason VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    resolution TEXT,
    CONSTRAINT fk_review_contractor FOREIGN KEY (candidate_contractor_id)
        REFERENCES contractors(id) ON DELETE SET NULL
);
