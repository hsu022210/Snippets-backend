set -o errexit

pip install -r requirements.txt

#!/bin/bash

DB_NAME="snippets_db_ut3z"
DB_USER="postgres"  # or your DB superuser

echo "Terminating all connections to $DB_NAME..."
psql -h $DATABASE_URL -U postgres -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'snippets_db_ut3z' AND pid <> pg_backend_pid();"


echo "Resetting database..."
python manage.py reset_db --noinput

python manage.py collectstatic --no-input

python manage.py makemigrations

python manage.py migrate


if [[ $CREATE_SUPERUSER == "True" ]];
then
    python manage.py createsuperuser --no-input
fi