-- Migration: Add new tables for Share Conversation, User Preferences, and enhanced features
-- Date: 2025-12-10
-- Description: Sprint 2 & 3 implementations

-- Table: shared_conversations
CREATE TABLE IF NOT EXISTS shared_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    share_id VARCHAR(32) UNIQUE NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL,
    title VARCHAR(255),
    messages TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    view_count INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_shared_conversations_share_id ON shared_conversations(share_id);
CREATE INDEX idx_shared_conversations_session_id ON shared_conversations(session_id);
CREATE INDEX idx_shared_conversations_user_id ON shared_conversations(user_id);

-- Table: user_preferences
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    key VARCHAR(100) NOT NULL,
    value TEXT NOT NULL,
    context TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    UNIQUE(user_id, key)
);

CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX idx_user_preferences_key ON user_preferences(key);

-- Add comments
COMMENT ON TABLE shared_conversations IS 'Stores publicly shared conversations with expiration and view tracking';
COMMENT ON TABLE user_preferences IS 'Stores user-specific preferences and persistent memory for personalization';

COMMENT ON COLUMN shared_conversations.share_id IS 'Unique public identifier for sharing';
COMMENT ON COLUMN shared_conversations.messages IS 'JSON string containing conversation messages';
COMMENT ON COLUMN shared_conversations.view_count IS 'Number of times this shared conversation has been viewed';
COMMENT ON COLUMN user_preferences.key IS 'Preference key (e.g., preferred_chart_type, theme)';
COMMENT ON COLUMN user_preferences.value IS 'Preference value stored as text';
COMMENT ON COLUMN user_preferences.context IS 'Optional context or metadata about the preference';
