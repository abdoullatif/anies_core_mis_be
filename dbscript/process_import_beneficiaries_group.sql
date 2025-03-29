-- FUNCTION: public.process_import_beneficiaries_group(uuid, uuid, uuid)

-- DROP FUNCTION IF EXISTS public.process_import_beneficiaries_group(uuid, uuid, uuid);

CREATE OR REPLACE FUNCTION public.process_import_beneficiaries_group(
	current_upload_id uuid,
	useruuid uuid,
	benefitplan uuid)
    RETURNS void
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
AS $BODY$
DECLARE
    failing_entries_first_name UUID[];
    failing_entries_last_name UUID[];
    failing_entries_dob UUID[];
BEGIN
    -- Vérifier la présence des champs obligatoires
    SELECT ARRAY_AGG("UUID") INTO failing_entries_first_name
    FROM individual_individualdatasource
    WHERE upload_id = current_upload_id AND individual_id IS NULL AND "isDeleted" = FALSE
    AND NOT "Json_ext" ? 'first_name';

    SELECT ARRAY_AGG("UUID") INTO failing_entries_last_name
    FROM individual_individualdatasource
    WHERE upload_id = current_upload_id AND individual_id IS NULL AND "isDeleted" = FALSE
    AND NOT "Json_ext" ? 'last_name';

    SELECT ARRAY_AGG("UUID") INTO failing_entries_dob
    FROM individual_individualdatasource
    WHERE upload_id = current_upload_id AND individual_id IS NULL AND "isDeleted" = FALSE
    AND NOT "Json_ext" ? 'dob';

    -- Gérer les erreurs si des champs obligatoires sont manquants
    IF failing_entries_first_name IS NOT NULL OR failing_entries_last_name IS NOT NULL OR failing_entries_dob IS NOT NULL THEN
        UPDATE individual_individualdatasourceupload
        SET error = COALESCE(error, '{}'::jsonb) || jsonb_build_object(
            'errors', jsonb_build_object(
                'error', 'Invalid entries',
                'timestamp', NOW()::TEXT,
                'upload_id', current_upload_id::TEXT,
                'failing_entries_first_name', failing_entries_first_name,
                'failing_entries_last_name', failing_entries_last_name,
                'failing_entries_dob', failing_entries_dob
            )
        ), status = 'FAIL'
        WHERE "UUID" = current_upload_id;

    ELSE
        BEGIN
            -- Insérer les nouveaux individus
            WITH new_entry AS (
                INSERT INTO individual_individual(
                    "UUID", "isDeleted", version, "UserCreatedUUID", "UserUpdatedUUID",
                    "Json_ext", first_name, last_name, dob, location_id
                )
                SELECT gen_random_uuid(), FALSE, 1, userUUID, userUUID,
                    "Json_ext",
                    "Json_ext"->>'first_name',
                    "Json_ext"->>'last_name',
                    TO_DATE("Json_ext"->>'dob', 'YYYY-MM-DD'),
                    loc."LocationId"
                FROM individual_individualdatasource AS ds
                LEFT JOIN "tblLocations" AS loc
                    ON loc."LocationName" = ds."Json_ext"->>'location_name'
                    AND loc."LocationCode" = ds."Json_ext"->>'location_code'
                    AND loc."LocationType" = 'V'
                    AND loc."ValidityTo" IS NULL
                WHERE ds.upload_id = current_upload_id
                    AND ds.individual_id IS NULL
                    AND ds."isDeleted" = FALSE
                RETURNING "UUID", "Json_ext"
            )
            -- Mise à jour de la table de source avec l'ID du nouvel individu
            UPDATE individual_individualdatasource
            SET individual_id = new_entry."UUID"
            FROM new_entry
            WHERE upload_id = current_upload_id
                AND individual_id IS NULL
                AND "isDeleted" = FALSE
                AND individual_individualdatasource."Json_ext" = new_entry."Json_ext";

            -- Mettre à jour l'état du processus d'importation
            UPDATE individual_individualdatasourceupload
            SET status = 'SUCCESS', error = '{}'
            WHERE "UUID" = current_upload_id;

        EXCEPTION WHEN OTHERS THEN
            -- Gestion des erreurs de transaction
            UPDATE individual_individualdatasourceupload
            SET status = 'FAIL'
            WHERE "UUID" = current_upload_id;

            UPDATE individual_individualdatasourceupload
            SET error = COALESCE(error, '{}'::jsonb) || jsonb_build_object(
                'errors', jsonb_build_object(
                    'error', SQLERRM,
                    'timestamp', NOW()::TEXT,
                    'upload_id', current_upload_id::TEXT
                )
            )
            WHERE "UUID" = current_upload_id;
        END;
    END IF;
END
$BODY$;

ALTER FUNCTION public.process_import_beneficiaries_group(uuid, uuid, uuid)
    OWNER TO postgres;
