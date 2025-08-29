# Bundle mapping & schémas Kobo → Ticket

Contenu :
- ticket_field_mapping_fixture.json (fixture Django KoboFieldMapping)
- ticket_field_mapping.csv (CSV éditable)
- ticket_ingestion.schema.json (schéma de validation des champs Ticket)
- ticket_extras.schema.json (schéma de validation de json_ext)

IMPORTANT : Remplace `REPLACE_WITH_KOBO_FORM_UUID` par l'UUID/PK réel de votre KoboForm avant `loaddata`.

## Import (fixtures)
python manage.py loaddata ticket_field_mapping_fixture.json
