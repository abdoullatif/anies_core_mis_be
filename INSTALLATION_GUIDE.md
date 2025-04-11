# Installation Guide du CoreMIS en local

## Étapes

1. Accéder au répertoire du projet :
   ```bash
   cd anies_core_mis_be
   ```

2. Installer les dépendances principales :
   ```bash
   pip install -r requirements.txt
   ```

3. Générer le fichier `modules-requirements.txt` :
   ```bash
   python modules-requirements.py ./dev-openimis.json > modules-requirements.txt
   ```
#### Pour les environnements de TEST ou de PROD remplacer dev-openimis.json par openimis.json
   ```bash
   python modules-requirements.py ./openimis.json > modules-requirements.txt
   ```

4. Installer les modules du CoreMIS :
   ```bash
   pip install -r modules-requirements.txt
   ```

5. Créer la base de données dans PostgreSQL.

6. Importer le contenu du fichier SQL :
   ```bash
   psql -U <user> -d <database_name> -f dbscript/emptyDatabase.sql
   ```

7. Créer le fichier `.env` en copiant `.env.example` :
   ```bash
   cp .env.example .env
   ```

   - Mettre à jour les informations de connexion à la base PostgreSQL.
   - **Assurez-vous que les deux lignes suivantes sont bien commentées :**
     ```dotenv
     # SCHEDULER_AUTOSTART=True
     # AUTO_PROVISIONING_USER_GROUP=True
     ```

8. Depuis le répertoire `openIMIS/`, exécuter la migration :
   ```bash
   python manage.py migrate
   ```

   - Vous verrez probablement ces messages d'erreur, c'est normal :
     ```
     core.models.base: Failed to load claim_sampling configuration, using default!
     ProgrammingError: ERREUR:  la relation « core_ModuleConfiguration » n'existe pas
     LINE 1: ...ore_ModuleConfiguration"."is_disabled_until" FROM "core_Modu...
     ```
   - Patientez jusqu’à la fin de la migration.

9. Décommenter les deux lignes suivantes dans le fichier `.env` :
   ```dotenv
   SCHEDULER_AUTOSTART=True
   AUTO_PROVISIONING_USER_GROUP=True
   ```

10. Démarrer le serveur :
    ```bash
    python manage.py runserver
    ```

11. Créer un utilisateur administrateur :
    ```bash
    python manage.py createsuperuser
    python manage.py changepassword <username>
    ```

12. Exécuter les scripts SQL supplémentaires depuis le répertoire `dbscript` :
    ```bash
    psql -U <user> -d <database_name> -f dbscript/process_import_beneficiaries.sql
    psql -U <user> -d <database_name> -f dbscript/process_import_beneficiaries_group.sql
    ```

---

**Remarques** :
- Remplacez `<user>` et `<database_name>` par vos propres identifiants PostgreSQL.
- Assurez-vous que PostgreSQL est correctement configuré et accessible.
