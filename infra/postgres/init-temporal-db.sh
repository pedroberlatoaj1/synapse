#!/bin/bash
set -e

# Cria os 2 databases extras que o Temporal precisa.
# O db "synapse" (app) e criado pela env POSTGRES_DB do proprio container.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
  CREATE DATABASE temporal;
  CREATE DATABASE temporal_visibility;
EOSQL

echo "[init] databases 'temporal' e 'temporal_visibility' criados."
