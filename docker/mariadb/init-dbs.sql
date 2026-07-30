-- ============================================================
-- MariaDB 10.11 LTS — Multi-Database Initialization Script
-- Auto-executed on first container startup via docker-entrypoint
-- ============================================================

-- 1. Create independent logical databases with utf8mb4 collation
CREATE DATABASE IF NOT EXISTS `db_articles`
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS `db_users`
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS `db_analytics`
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. Create application user (non-root)
CREATE USER IF NOT EXISTS 'app_user'@'%' IDENTIFIED BY '${MARIADB_APP_PASSWORD}';

-- 3. Grant scoped privileges per database (least privilege principle)
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, INDEX, REFERENCES
  ON `db_articles`.* TO 'app_user'@'%';

GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, INDEX, REFERENCES
  ON `db_users`.* TO 'app_user'@'%';

GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, INDEX, REFERENCES
  ON `db_analytics`.* TO 'app_user'@'%';

FLUSH PRIVILEGES;
