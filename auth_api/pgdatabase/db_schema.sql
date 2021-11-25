-- Schema for content. Diagram at: https://dbdiagram.io/d/61274e986dc2bb6073bc3afe
CREATE SCHEMA IF NOT EXISTS app;

CREATE TYPE app.auth_event_type AS ENUM (
    'login',
    'logout'
);

CREATE TABLE IF NOT EXISTS app.users (
    user_id                 uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_login              text        NOT NULL,
    user_password           text        NOT NULL,
    user_email              text        NOT NULL,
    created_at              timestamp with time zone DEFAULT (now()),
    updated_at              timestamp with time zone DEFAULT (now())
) partition by hash(user_id);
create table app.users_0 partition of app.users for values with (modulus 10, remainder 0);
create table app.users_1 partition of app.users for values with (modulus 10, remainder 1);
create table app.users_2 partition of app.users for values with (modulus 10, remainder 2);
create table app.users_3 partition of app.users for values with (modulus 10, remainder 3);
create table app.users_4 partition of app.users for values with (modulus 10, remainder 4);
create table app.users_5 partition of app.users for values with (modulus 10, remainder 5);
create table app.users_6 partition of app.users for values with (modulus 10, remainder 6);
create table app.users_7 partition of app.users for values with (modulus 10, remainder 7);
create table app.users_8 partition of app.users for values with (modulus 10, remainder 8);
create table app.users_9 partition of app.users for values with (modulus 10, remainder 9);


CREATE TABLE IF NOT EXISTS app.auth_events (
    auth_event_id           uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_event_owner_id     uuid        NOT NULL,
    auth_event_type         app.auth_event_type,
    auth_event_time         timestamp with time zone DEFAULT (now()),
    auth_event_fingerprint  text        NOT NULL,
    FOREIGN KEY (auth_event_owner_id)
            REFERENCES app.users (user_id)
            ON DELETE CASCADE
            ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS app.tokens (
    token_id                uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    token_owner_id          uuid        NOT NULL,
    token_value             text        NOT NULL,
    token_used              boolean     DEFAULT false,
    created_at              timestamp with time zone DEFAULT (now()),
    expires_at              timestamp with time zone DEFAULT (now()::DATE + 10),
     UNIQUE (token_owner_id, token_value),
    FOREIGN KEY (token_owner_id)
            REFERENCES app.users(user_id)
            ON DELETE CASCADE
            ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS app.roles (
    role_id                 uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    role_name               text        NOT NULL,
    UNIQUE (role_name)
);

CREATE TABLE IF NOT EXISTS app.permissions (
    permission_id           uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    permission_name         text        NOT NULL,
    UNIQUE (permission_name)
);

CREATE TABLE IF NOT EXISTS app.role_permissions (
    role_permission_id      uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id                 uuid        NOT NULL,
    permission_id           uuid        NOT NULL,
     UNIQUE (role_id, permission_id),
    FOREIGN KEY (role_id)
            REFERENCES app.roles
            ON DELETE CASCADE
            ON UPDATE CASCADE,
    FOREIGN KEY (permission_id)
            REFERENCES app.permissions
            ON DELETE CASCADE
            ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS app.roles_owners (
    role_owner_id           uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id                uuid        NOT NULL,
    role_id                 uuid        NOT NULL,
     UNIQUE (owner_id, role_id),
    FOREIGN KEY (owner_id)
            REFERENCES app.users(user_id)
            ON DELETE CASCADE
            ON UPDATE CASCADE,
    FOREIGN KEY (role_id)
            REFERENCES app.roles
            ON DELETE CASCADE
            ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS app.social_accounts (
    social_account_id       uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 uuid        NOT NULL,
    social_id               text        NOT NULL,
    social_provider         text        NOT NULL,
     UNIQUE (social_id, social_provider),
    FOREIGN KEY (user_id)
            REFERENCES app.users(user_id)
            ON DELETE CASCADE
            ON UPDATE CASCADE
);

CREATE INDEX ON app.users(user_login);

CREATE INDEX ON app.users(user_email);

CREATE INDEX ON app.tokens(token_value);
