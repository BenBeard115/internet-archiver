-- This file contains table definitions for the database.
DROP TABLE IF EXISTS url CASCADE;
DROP TABLE IF EXISTS page_scrape CASCADE;

CREATE TABLE url (
    url_id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    visits INT,
    summary TEXT
);

CREATE TABLE page_scrape
(
    id SERIAL PRIMARY KEY,
    url_id INT NOT NULL,
    at TIMESTAMP NOT NULL,
    html TEXT NOT NULL,
    CSS TEXT NOT NULL,
    FOREIGN KEY (url_id) REFERENCES url(url_id)
);
