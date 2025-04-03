# run code import
from django.core.management.base import BaseCommand
from django.db import connection
import os
from pathlib import Path

class Command(BaseCommand):
    help = 'Exécute les scripts SQL pour import des bénéficiaires'

    def handle(self, *args, **options):
        # Chemin absolu plus robuste
        base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
        scripts = [
            base_dir / 'dbscript' / 'process_import_beneficiaries.sql',
            base_dir / 'dbscript' / 'process_import_beneficiaries_group.sql'
        ]

        for script_path in scripts:
            try:
                if not script_path.exists():
                    raise FileNotFoundError(f"Script introuvable: {script_path}")

                self.stdout.write(f"Exécution du script: {script_path.name}...")
                
                with connection.cursor() as cursor:
                    with open(script_path, 'r') as f:
                        sql = f.read()
                        cursor.execute(sql)
                
                self.stdout.write(
                    self.style.SUCCESS(f"Script {script_path.name} exécuté avec succès")
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Erreur lors de l'exécution de {script_path.name}: {str(e)}")
                )
                # Optionnel: arrêter l'exécution si un script échoue
                # return


# python manage.py run_sql_script