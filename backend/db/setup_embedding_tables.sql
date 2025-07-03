-- Create user_embedding table to store user embeddings
CREATE TABLE IF NOT EXISTS user_embedding (
    uuid TEXT NOT NULL,
    embedding FLOAT8[] NOT NULL,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (uuid, version)
);

-- Create item_embedding table to store item embeddings  
CREATE TABLE IF NOT EXISTS item_embedding (
    item_id TEXT PRIMARY KEY,
    embedding FLOAT8[] NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_embedding_uuid ON user_embedding(uuid);
CREATE INDEX IF NOT EXISTS idx_user_embedding_version ON user_embedding(version DESC);
CREATE INDEX IF NOT EXISTS idx_item_embedding_item_id ON item_embedding(item_id);

-- Add foreign key constraints if the referenced tables exist
DO $$
BEGIN
    -- Check if user_profile table exists, then add foreign key
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_profile') THEN
        ALTER TABLE user_embedding 
        ADD CONSTRAINT fk_user_embedding_uuid 
        FOREIGN KEY (uuid) REFERENCES user_profile(uuid) 
        ON DELETE CASCADE;
    END IF;
    
    -- Check if item table exists, then add foreign key
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'item') THEN
        ALTER TABLE item_embedding 
        ADD CONSTRAINT fk_item_embedding_item_id 
        FOREIGN KEY (item_id) REFERENCES item(item_id) 
        ON DELETE CASCADE;
    END IF;
EXCEPTION
    WHEN duplicate_object THEN
        -- Foreign key constraints already exist, ignore
        NULL;
END $$;

-- Add comments for documentation
COMMENT ON TABLE user_embedding IS 'Stores user preference embeddings with versioning';
COMMENT ON TABLE item_embedding IS 'Stores item content embeddings for similarity matching';
COMMENT ON COLUMN user_embedding.version IS 'Version number for tracking embedding updates';
COMMENT ON COLUMN user_embedding.embedding IS 'User preference vector (typically 1536 dimensions for OpenAI embeddings)';
COMMENT ON COLUMN item_embedding.embedding IS 'Item content vector (typically 1536 dimensions for OpenAI embeddings)';