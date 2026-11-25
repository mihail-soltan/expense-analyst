CREATE EXTENSION pgcrypto;

CREATE TABLE users (
    user_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    role VARCHAR(20),
    is_active BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE TABLE workspaces (
    workspace_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(50),
    owner_id INTEGER NOT NULL,
    FOREIGN KEY(owner_id) REFERENCES users(user_id), 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE TABLE workspace_members (
    workspace_id INTEGER NOT NULL,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(workspace_id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    PRIMARY KEY (workspace_id, user_id)
);

CREATE TABLE IF NOT EXISTS conversations (
    conversation_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    workspace_id INTEGER NOT NULL,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(workspace_id),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    model TEXT NOT NULL,
    instructions TEXT NOT NULL,
    prompt TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    response_time FLOAT NOT NULL,
    cost FLOAT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE TABLE categories (
    category_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    workspace_id INTEGER NOT NULL,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(workspace_id),
    name VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE TABLE incomes (
    income_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    workspace_id INTEGER NOT NULL,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(workspace_id),
    date DATE,
    source TEXT,
    amount NUMERIC(10,2) CONSTRAINT income_chk_positive CHECK (amount > 0),
    description TEXT,
    invoice_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE TABLE expenses (
    expense_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    workspace_id INTEGER NOT NULL,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(workspace_id),
    category_id INTEGER,
    FOREIGN KEY (category_id) REFERENCES categories(category_id),
    date DATE,
    item TEXT,
    amount NUMERIC(10,2) CONSTRAINT expense_chk_positive CHECK (amount > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE TABLE feedback (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(conversation_id),
    source TEXT NOT NULL,
    relevance TEXT,
    explanation TEXT,
    score INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
);


-- CREATES DEFAULT WORKSPACE WHEN NEW USER IS INSERTED
CREATE OR REPLACE FUNCTION create_workspace()  
RETURNS TRIGGER AS $create_workspace$ 
	BEGIN
		INSERT INTO workspaces(owner_id, name) VALUES (new.user_id, 'default_workspace');
		RETURN NEW;
	END;
$create_workspace$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER workspace_trigger
AFTER INSERT ON users
FOR EACH ROW EXECUTE FUNCTION create_workspace();
------------------------------------------------------

-- ADD WORKSPACE OWNER AS MEMBER
CREATE OR REPLACE FUNCTION add_wksp_owner_as_member()
RETURNS TRIGGER AS $add_wksp_owner_as_member$ 
	BEGIN
		INSERT INTO workspace_members(workspace_id, user_id) VALUES (new.workspace_id, new.owner_id);
		RETURN NEW;
	END;
$add_wksp_owner_as_member$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER add_wksp_owner_as_member_trg
AFTER INSERT ON workspaces
FOR EACH ROW EXECUTE FUNCTION add_wksp_owner_as_member();
-------------------------------------------------------

INSERT INTO users(
    username,
    email,
    password_hash
) VALUES (
    'admin',
    'admin@example.com',
    crypt('password', gen_salt('bf', 8))
);

-- POLICIES
CREATE POLICY workspace_expenses_policy
    ON expenses
    TO app_user
    USING (
        workspace_id = NULLIF(current_setting('rls.workspace_id', true), '')::integer
        
        AND EXISTS (
            SELECT 1
            FROM workspace_members
            WHERE workspace_members.workspace_id = expenses.workspace_id
            AND workspace_members.user_id  = NULLIF(current_setting('rls.user_id', true), '')::integer
        )
    );

CREATE POLICY workspace_incomes_policy
    ON incomes
    TO app_user
    USING (
        workspace_id = NULLIF(current_setting('rls.workspace_id', true), '')::integer

        AND EXISTS (
            SELECT 1
            FROM workspace_members
            WHERE workspace_members.workspace_id = incomes.workspace_id
            AND workspace_members.user_id  = NULLIF(current_setting('rls.user_id', true), '')::integer
        )
    );

CREATE POLICY workspace_conversations_policy
    ON conversations
    TO app_user
    USING (
        workspace_id = NULLIF(current_setting('rls.workspace_id', true), '')::integer

        AND EXISTS (
            SELECT 1
            FROM workspace_members
            WHERE workspace_members.workspace_id = conversations.workspace_id
            AND workspace_members.user_id  = NULLIF(current_setting('rls.user_id', true), '')::integer
        )
    );

CREATE POLICY workspace_categories_policy
    ON categories
    TO app_user
    USING (
        workspace_id = NULLIF(current_setting('rls.workspace_id', true), '')::integer

        AND EXISTS (
            SELECT 1
            FROM workspace_members
            WHERE workspace_members.workspace_id = categories.workspace_id
            AND workspace_members.user_id  = NULLIF(current_setting('rls.user_id', true), '')::integer
        )
    );

CREATE POLICY user_workspaces_policy
    ON workspaces
    TO app_user
    USING (
        EXISTS (
            SELECT 1
            FROM workspace_members
            WHERE workspace_members.workspace_id = workspaces.workspace_id
            AND workspace_members.user_id  = NULLIF(current_setting('rls.user_id', true), '')::integer
        )
    );

CREATE POLICY workspace_members_policy
    ON workspace_members
    TO app_user
    USING (
        workspace_id = NULLIF(current_setting('rls.workspace_id', true), '')::integer
    );

CREATE POLICY users_policy
	ON users
	TO app_user
	USING (
		user_id = NULLIF(current_setting('rls.user_id', true), '')::integer
	)

ALTER TABLE expenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE incomes ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspace_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

GRANT SELECT, INSERT, UPDATE, DELETE ON expenses TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON incomes TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON categories TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON conversations TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON workspaces TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON workspace_members TO app_user;

CREATE OR REPLACE FUNCTION get_user_for_auth(p_username TEXT)
RETURNS TABLE (
    user_id INTEGER,
    username TEXT,
    email TEXT,
    password_hash TEXT
)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT user_id, username, email, password_hash
    FROM users
    WHERE username = p_username;
$$;

REVOKE ALL ON FUNCTION get_user_for_auth(TEXT) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION get_user_for_auth(TEXT) TO app_user;


-- AUTH

CREATE TABLE refresh_tokens (
    token_hash TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE POLICY refresh_tokens_policy
    ON refresh_tokens
    TO app_user
    USING (
        user_id = NULLIF(current_setting('rls.user_id', true), '')::integer
    )
    WITH CHECK (
        user_id = NULLIF(current_setting('rls.user_id', true), '')::integer
    );

ALTER TABLE refresh_tokens ENABLE ROW LEVEL SECURITY;

GRANT SELECT, INSERT, UPDATE ON refresh_tokens TO app_user;

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);

CREATE OR REPLACE FUNCTION rotate_refresh_token(
    p_old_token_hash TEXT,
    p_new_token_hash TEXT,
    p_new_expires_at TIMESTAMPTZ
)
RETURNS TABLE (
    user_id INTEGER,
    username TEXT,
    email TEXT,
    status TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_record RECORD;
BEGIN
    SELECT rt.user_id, rt.expires_at, rt.revoked, u.username, u.email
    INTO v_record
    FROM refresh_tokens rt
    JOIN users u ON u.user_id = rt.user_id
    WHERE rt.token_hash = p_old_token_hash
    FOR UPDATE;

    IF NOT FOUND THEN
        RETURN QUERY SELECT NULL::INTEGER, NULL::TEXT, NULL::TEXT, 'invalid'::TEXT;
        RETURN;
    END IF;

    -- if an already-revoked token is used, revoke ALL tokens for this user
    IF v_record.revoked THEN
        UPDATE refresh_tokens SET revoked = TRUE WHERE refresh_tokens.user_id = v_record.user_id;
        RETURN QUERY SELECT NULL::INTEGER, NULL::TEXT, NULL::TEXT, 'reused'::TEXT;
        RETURN;
    END IF;

    IF v_record.expires_at < NOW() THEN
        RETURN QUERY SELECT NULL::INTEGER, NULL::TEXT, NULL::TEXT, 'expired'::TEXT;
        RETURN;
    END IF;

    -- Mark old token as revoked and insert the rotated replacement
    UPDATE refresh_tokens SET revoked = TRUE WHERE token_hash = p_old_token_hash;

    INSERT INTO refresh_tokens (token_hash, user_id, expires_at)
    VALUES (p_new_token_hash, v_record.user_id, p_new_expires_at);

    RETURN QUERY SELECT v_record.user_id, v_record.username, v_record.email, 'ok'::TEXT;
END;
$$;

REVOKE ALL ON FUNCTION rotate_refresh_token(TEXT, TEXT, TIMESTAMPTZ) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION rotate_refresh_token(TEXT, TEXT, TIMESTAMPTZ) TO app_user;