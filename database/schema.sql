-- This file contains table definitions for the database.
DROP TABLE IF EXISTS url CASCADE;
DROP TABLE IF EXISTS interaction_type CASCADE;
DROP TABLE IF EXISTS user_interaction CASCADE;
DROP TABLE IF EXISTS page_scrape CASCADE;


CREATE TABLE url (
    url_id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    summary TEXT,
    genre TEXT
);


CREATE TABLE interaction_type(
    type_id SERIAL PRIMARY KEY,
    type TEXT NOT NULL
);


CREATE TABLE user_interaction(
    interaction_id SERIAL PRIMARY KEY,
    url_id INT NOT NULL,
    type_id INT NOT NULL,
    interact_at TIMESTAMP NOT NULL,
    FOREIGN KEY (url_id) REFERENCES url(url_id),
    FOREIGN KEY (type_id) REFERENCES interaction_type(type_id)
);

CREATE TABLE page_scrape
(
    page_scrape_id SERIAL PRIMARY KEY,
    url_id INT NOT NULL,
    scrape_at TIMESTAMP NOT NULL,
    html_s3_ref TEXT NOT NULL,
    css_s3_ref TEXT NOT NULL,
    screenshot_s3_ref TEXT NOT NULL,
    is_human BOOLEAN NOT NULL,
    FOREIGN KEY (url_id) REFERENCES url(url_id)
);


INSERT INTO interaction_type (type)
VALUES ('visit'),
        ('save')
;