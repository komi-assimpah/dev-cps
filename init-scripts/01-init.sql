CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

CREATE TABLE appartement (
  id          SERIAL PRIMARY KEY,  -- Auto-incrément
  etage       INTEGER,
  orientation TEXT,                -- Ex: 'Sud', 'Nord-Est'
  surface     DOUBLE PRECISION
);

CREATE TABLE scores (
  time        TIMESTAMPTZ NOT NULL,
  appart_id   INTEGER     NOT NULL,
  IAQ_2H    DOUBLE PRECISION,
  IIT_2H    DOUBLE PRECISION,
  CONSTRAINT pk_scores PRIMARY KEY (time, appart_id),
  CONSTRAINT fk_appart FOREIGN KEY (appart_id) REFERENCES appartement(id)
);

SELECT create_hypertable('scores', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS ix_scores_appart_time ON scores (appart_id, time DESC);
INSERT INTO appartement (etage, orientation, surface) VALUES (0, 'Ouest', 255);

-- pour les tests, devra degager par pitié
INSERT INTO scores (time, appart_id, IAQ_2H, IIT_2H) VALUES (to_timestamp(1766962800), 1, 0.4, 100.0);
INSERT INTO scores (time, appart_id, IAQ_2H, IIT_2H) VALUES (to_timestamp(1766970000), 1, 0.6, 100.0);
INSERT INTO scores (time, appart_id, IAQ_2H, IIT_2H) VALUES (to_timestamp(1766977200), 1, 0.5, 100.0);
INSERT INTO scores (time, appart_id, IAQ_2H, IIT_2H) VALUES (to_timestamp(1766984400), 1, 0.8, 100.0);
INSERT INTO scores (time, appart_id, IAQ_2H, IIT_2H) VALUES (to_timestamp(1766991600), 1, 1.0, 100.0);
INSERT INTO scores (time, appart_id, IAQ_2H, IIT_2H) VALUES (to_timestamp(1766998800), 1, 1.2, 100.0);