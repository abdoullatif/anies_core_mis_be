-- FUNCTION: public.process_import_beneficiaries(uuid, uuid, uuid)

-- DROP FUNCTION IF EXISTS public.process_import_beneficiaries(uuid, uuid, uuid);

CREATE OR REPLACE FUNCTION public.process_import_beneficiaries(
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
    failing_entries_invalid_json UUID[];
    json_schema JSONB;
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

    -- Vérifier la validité des données JSON
    SELECT beneficiary_data_schema INTO json_schema
    FROM social_protection_benefitplan
    WHERE "UUID" = benefitPlan;

    --SELECT ARRAY_AGG("UUID") INTO failing_entries_invalid_json
    --FROM individual_individualdatasource
    --WHERE upload_id = current_upload_id AND individual_id IS NULL AND "isDeleted" = FALSE;

    -- Gérer les erreurs et arrêter l'import si nécessaire
    IF failing_entries_invalid_json IS NOT NULL OR failing_entries_first_name IS NOT NULL
        OR failing_entries_last_name IS NOT NULL OR failing_entries_dob IS NOT NULL THEN

        UPDATE individual_individualdatasourceupload
        SET error = COALESCE(error, '{}'::jsonb) || jsonb_build_object(
            'errors', jsonb_build_object(
                'error', 'Invalid entries',
                'timestamp', NOW()::TEXT,
                'upload_id', current_upload_id::TEXT,
                'failing_entries_first_name', failing_entries_first_name,
                'failing_entries_last_name', failing_entries_last_name,
                'failing_entries_dob', failing_entries_dob,
                'failing_entries_invalid_json', failing_entries_invalid_json
            )
        ), status = 'FAIL'
        WHERE "UUID" = current_upload_id;

    ELSE
        BEGIN
            -- Insertion des nouveaux individus
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
            -- Mettre à jour les sources avec l'ID de l'individu
            UPDATE individual_individualdatasource
            SET individual_id = new_entry."UUID"
            FROM new_entry
            WHERE upload_id = current_upload_id
                AND individual_id IS NULL
                AND "isDeleted" = FALSE
                AND individual_individualdatasource."Json_ext" = new_entry."Json_ext";

            -- Insérer les bénéficiaires
            INSERT INTO social_protection_beneficiary(
                "UUID", "isDeleted", "Json_ext", "DateCreated", "DateUpdated", version,
                "DateValidFrom", "DateValidTo", status, "benefit_plan_id", "individual_id",
                "UserCreatedUUID", "UserUpdatedUUID"
            )
            SELECT gen_random_uuid(), FALSE, iids."Json_ext" - 'first_name' - 'last_name' - 'dob',
                NOW(), NOW(), 1, NOW(), NULL, 'POTENTIAL', benefitPlan, new_entry."UUID", userUUID, userUUID
            FROM individual_individualdatasource iids
            RIGHT JOIN individual_individual new_entry
            ON new_entry."UUID" = iids.individual_id
            WHERE iids.upload_id = current_upload_id
                AND iids."isDeleted" = FALSE;

            -- Mise à jour du statut de l'import
            UPDATE individual_individualdatasourceupload
            SET status = 'SUCCESS', error = '{}'
            WHERE "UUID" = current_upload_id;

        EXCEPTION WHEN OTHERS THEN
            -- Gérer les erreurs de transaction
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

ALTER FUNCTION public.process_import_beneficiaries(uuid, uuid, uuid)
    OWNER TO postgres;
