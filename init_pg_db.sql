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