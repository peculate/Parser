START TRANSACTION;

SET CONSTRAINTS ALL DEFERRED;

CREATE TABLE Level (
    course_id   CHARACTER(19)           PRIMARY KEY,
    title       CHARACTER VARYING(100)  DEFAULT 'No title provided',
    author      CHARACTER VARYING(100)  DEFAULT 'Anonymous',
    skin        CHARACTER VARYING(12)   NOT NULL,
    scene       CHARACTER VARYING(11)   NOT NULL,
    region      CHARACTER VARYING(3)    NOT NULL,
    country     CHARACTER VARYING(3)    DEFAULT 'N/A',
    tag         CHARACTER VARYING(12)   DEFAULT 'N/A'
    difficulty  CHARACTER VARYING(12)   NOT NULL,
    uploaded    DATE                    NOT NULL,
    plays       INTEGER                 NOT NULL,
    likes       INTEGER                 DEFAULT 0,
    clears      INTEGER                 DEFAULT 0,
    attempts    INTEGER                 DEFAULT 0,
    shares      SMALLINT                DEFAULT 0,
    thumb_url   CHARACTER(60)           DEFAULT 'N/A',
    full_url    CHARACTER(65)           DEFAULT 'N/A'
);

COPY Level         FROM 'smm.csv'             CSV;

COMMIT;