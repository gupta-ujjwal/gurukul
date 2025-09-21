{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.python3
    pkgs.postgresql
    pkgs.python3Packages.pip
    pkgs.python3Packages.virtualenv
    pkgs.python3Packages.setuptools
    pkgs.python3Packages.wheel
  ];

  shellHook = ''
    export PGDATA=$PWD/postgres_data
    export PGHOST=$PWD/postgres
    export PGDATABASE=learning_agent
    export PGUSER=postgres
    export PGPASSWORD=password
    
    # Find and add pg_config to PATH
    PG_CONFIG_PATH=$(find /nix/store -name pg_config -type f -executable | head -1)
    if [ -n "$PG_CONFIG_PATH" ]; then
      export PATH="$(dirname $PG_CONFIG_PATH):$PATH"
      echo "pg_config found at: $PG_CONFIG_PATH"
    else
      echo "pg_config not found"
    fi
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
      source venv/bin/activate
      echo "Virtual environment activated"
    fi
    
    echo "PostgreSQL development environment ready"
  '';
}