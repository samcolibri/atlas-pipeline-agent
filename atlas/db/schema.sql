-- ATLAS State Store — Supabase/Postgres schema
-- Run this once to initialize the database.
-- Supabase auto-generates REST APIs from this schema.

-- ── Accounts ─────────────────────────────────────────────────────────────────
-- Every institution from FDIC/NCUA. Source of truth for the account universe.

CREATE TABLE IF NOT EXISTS accounts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cert_id         TEXT NOT NULL,          -- FDIC cert or NCUA charter number
    source          TEXT NOT NULL,          -- 'fdic' | 'ncua'
    name            TEXT NOT NULL,
    city            TEXT,
    state           TEXT,
    zip_code        TEXT,
    address         TEXT,
    asset_k         BIGINT,                 -- total assets in $thousands
    website         TEXT,
    domain          TEXT,                   -- extracted from website
    phone           TEXT,
    established     TEXT,
    institution_type TEXT,                  -- 'bank' | 'credit_union' | 'savings'

    -- Pipeline state
    status          TEXT NOT NULL DEFAULT 'new',
    -- new | enriching | enriched | suppressed | queued | sent | replied | booked | dead

    suppressed      BOOLEAN DEFAULT FALSE,
    suppression_reason TEXT,               -- 'customer' | 'active_opp' | 'dnc' | 'competitor'

    -- Trigger signals
    has_trigger     BOOLEAN DEFAULT FALSE,
    trigger_type    TEXT,                  -- 'job_posting' | 'merger' | 'asset_growth' | 'intent'
    trigger_detail  TEXT,
    trigger_date    TIMESTAMPTZ,

    -- Timestamps
    first_seen_at   TIMESTAMPTZ DEFAULT NOW(),
    enriched_at     TIMESTAMPTZ,
    last_activity   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(cert_id, source)
);

CREATE INDEX idx_accounts_status   ON accounts(status);
CREATE INDEX idx_accounts_state    ON accounts(state);
CREATE INDEX idx_accounts_type     ON accounts(institution_type);
CREATE INDEX idx_accounts_trigger  ON accounts(has_trigger) WHERE has_trigger = TRUE;
CREATE INDEX idx_accounts_domain   ON accounts(domain) WHERE domain IS NOT NULL;


-- ── Contacts ──────────────────────────────────────────────────────────────────
-- Enriched contacts from Waterfall.io/ZoomInfo. One account → many contacts.

CREATE TABLE IF NOT EXISTS contacts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id      UUID REFERENCES accounts(id) ON DELETE CASCADE,

    first_name      TEXT,
    last_name       TEXT,
    full_name       TEXT,
    title           TEXT,
    email           TEXT,
    phone           TEXT,
    linkedin_url    TEXT,

    -- Persona classification
    persona         TEXT,                  -- 'hr_executive' | 'l&d' | 'compliance' | 'bsa' | 'ops'
    is_target_persona BOOLEAN DEFAULT FALSE,

    -- Email validation
    email_status    TEXT,                  -- zerobounce status: valid | invalid | catch-all | ...
    email_validated BOOLEAN DEFAULT FALSE,
    email_validated_at TIMESTAMPTZ,

    -- Enrichment source
    enriched_by     TEXT,                  -- 'waterfall' | 'zoominfo' | 'apollo'
    enrichment_confidence FLOAT,

    -- Contact state
    status          TEXT DEFAULT 'new',    -- new | validated | queued | sent | replied | suppressed
    suppressed      BOOLEAN DEFAULT FALSE,
    suppression_reason TEXT,

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(email)
);

CREATE INDEX idx_contacts_account     ON contacts(account_id);
CREATE INDEX idx_contacts_status      ON contacts(status);
CREATE INDEX idx_contacts_persona     ON contacts(is_target_persona) WHERE is_target_persona = TRUE;
CREATE INDEX idx_contacts_email_ok    ON contacts(email_validated) WHERE email_validated = TRUE;


-- ── Outreach attempts ─────────────────────────────────────────────────────────
-- Every email/LinkedIn touch. Audit trail for every send.

CREATE TABLE IF NOT EXISTS outreach_attempts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_id      UUID REFERENCES contacts(id) ON DELETE CASCADE,
    account_id      UUID REFERENCES accounts(id) ON DELETE CASCADE,

    channel         TEXT NOT NULL,         -- 'email' | 'linkedin'
    sequence_step   INTEGER DEFAULT 1,

    -- Email fields
    instantly_lead_id   TEXT,
    instantly_campaign_id TEXT,
    subject         TEXT,
    body_preview    TEXT,                  -- first 500 chars

    -- Send state
    status          TEXT DEFAULT 'pending',
    -- pending | sent | delivered | opened | clicked | replied | bounced | unsubscribed

    sent_at         TIMESTAMPTZ,
    opened_at       TIMESTAMPTZ,
    replied_at      TIMESTAMPTZ,
    bounced_at      TIMESTAMPTZ,

    -- ATLAS mode at time of send
    atlas_mode      TEXT,                  -- 'shadow' | 'review' | 'auto'

    -- Human approval gate
    approved_by     TEXT,
    approved_at     TIMESTAMPTZ,

    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_attempts_contact  ON outreach_attempts(contact_id);
CREATE INDEX idx_attempts_account  ON outreach_attempts(account_id);
CREATE INDEX idx_attempts_status   ON outreach_attempts(status);
CREATE INDEX idx_attempts_sent     ON outreach_attempts(sent_at) WHERE sent_at IS NOT NULL;


-- ── Replies ───────────────────────────────────────────────────────────────────
-- Every inbound reply, classified by Claude.

CREATE TABLE IF NOT EXISTS replies (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attempt_id      UUID REFERENCES outreach_attempts(id),
    contact_id      UUID REFERENCES contacts(id),
    account_id      UUID REFERENCES accounts(id),

    -- Raw reply from Instantly webhook
    event_type      TEXT,                  -- instantly event type
    reply_text      TEXT,

    -- Claude classification
    classification  TEXT,
    -- 'positive' | 'objection' | 'wrong_person' | 'out_of_office' | 'unsubscribe' | 'referral'
    classification_confidence FLOAT,
    classified_at   TIMESTAMPTZ,

    -- Follow-up action taken
    action_taken    TEXT,                  -- 'calendly_sent' | 'objection_handled' | 'referral_asked' | 'suppressed'
    action_at       TIMESTAMPTZ,

    -- Booking
    meeting_booked  BOOLEAN DEFAULT FALSE,
    meeting_at      TIMESTAMPTZ,

    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_replies_contact        ON replies(contact_id);
CREATE INDEX idx_replies_classification ON replies(classification);
CREATE INDEX idx_replies_positive       ON replies(meeting_booked) WHERE meeting_booked = TRUE;


-- ── Suppression list ──────────────────────────────────────────────────────────
-- Hard exclusions. ATLAS never touches these accounts/contacts.

CREATE TABLE IF NOT EXISTS suppression_list (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scope           TEXT NOT NULL,         -- 'account' | 'contact' | 'domain'
    value           TEXT NOT NULL,         -- cert_id | email | domain
    reason          TEXT NOT NULL,
    -- 'customer' | 'active_opp' | 'dnc' | 'bounced' | 'unsubscribed'
    -- 'competitor' | 'partner' | 'bad_data' | 'rep_relationship'

    source          TEXT,                  -- 'salesforce' | 'manual' | 'atlas'
    added_at        TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(scope, value)
);

CREATE INDEX idx_suppression_value ON suppression_list(value);
CREATE INDEX idx_suppression_scope ON suppression_list(scope);


-- ── Trigger signals ───────────────────────────────────────────────────────────
-- Intent signals from free sources (job postings, mergers, asset growth).

CREATE TABLE IF NOT EXISTS triggers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id      UUID REFERENCES accounts(id) ON DELETE CASCADE,

    trigger_type    TEXT NOT NULL,         -- 'job_posting' | 'merger' | 'asset_growth' | 'regulatory'
    signal_detail   TEXT,
    signal_url      TEXT,
    signal_date     DATE,
    score           INTEGER DEFAULT 1,     -- 1-10, higher = more urgent

    processed       BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_triggers_account     ON triggers(account_id);
CREATE INDEX idx_triggers_unprocessed ON triggers(processed) WHERE processed = FALSE;
CREATE INDEX idx_triggers_type        ON triggers(trigger_type);


-- ── Audit log ─────────────────────────────────────────────────────────────────
-- Every action ATLAS takes. Immutable record.

CREATE TABLE IF NOT EXISTS audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type     TEXT,                  -- 'account' | 'contact' | 'outreach' | 'reply'
    entity_id       UUID,
    action          TEXT NOT NULL,         -- 'scout_pulled' | 'enriched' | 'validated' | 'sent' | 'classified'
    detail          JSONB,
    atlas_mode      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_entity  ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_action  ON audit_log(action);
CREATE INDEX idx_audit_time    ON audit_log(created_at);


-- ── Updated-at trigger ────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER accounts_updated_at BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER contacts_updated_at BEFORE UPDATE ON contacts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
