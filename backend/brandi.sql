CREATE DATABASE brandi default CHARACTER SET UTF8;

use brandi;

CREATE TABLE sellers(
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW()
) ENGINE=INNODB CHARSET=utf8;