from django.core.management.base import BaseCommand
from django.db import connection
from pathlib import Path
import os

class Command(BaseCommand):
    help = 'Exécute un script SQL spécifié en argument'

    def add_arguments(self, parser):
        parser.add_argument(
            'script_path',
            type=str,
            help='Chemin vers le fichier SQL à exécuter'
        )
        parser.add_argument(
            '--multi',
            action='store_true',
            help='Exécute tous les fichiers SQL du répertoire spécifié'
        )

    def handle(self, *args, **options):
        script_path = Path(options['script_path']).resolve()
        multi_mode = options['multi']

        try:
            if multi_mode:
                if not script_path.is_dir():
                    raise ValueError("Le chemin doit être un répertoire en mode multi")
                self.process_directory(script_path)
            else:
                if not script_path.is_file():
                    raise ValueError("Le chemin doit pointer vers un fichier")
                self.process_file(script_path)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur : {str(e)}"))
            return

    def process_file(self, file_path):
        self.stdout.write(f"Exécution du script : {file_path}...")
        
        with connection.cursor() as cursor:
            with open(file_path, 'r') as f:
                sql = f.read()
                cursor.execute(sql)
        
        self.stdout.write(
            self.style.SUCCESS(f"Script {file_path.name} exécuté avec succès")
        )

    def process_directory(self, dir_path):
        sql_files = sorted(dir_path.glob('*.sql'))
        
        if not sql_files:
            self.stdout.write(self.style.WARNING("Aucun fichier .sql trouvé"))
            return

        self.stdout.write(f"Exécution de {len(sql_files)} fichiers SQL...")
        
        for sql_file in sql_files:
            try:
                self.process_file(sql_file)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Échec sur {sql_file.name} : {str(e)}")
                )
                # Option : ajouter --continue pour ignorer les erreurs
                # if not options['continue']:
                #     raise


# TUTO

# python manage.py execute_sql /chemin/vers/script.sql

# python manage.py execute_sql /chemin/vers/dossier --multi