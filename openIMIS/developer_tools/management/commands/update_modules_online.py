#!/usr/bin/env python3
"""
Commande Django pour mettre à jour automatiquement les modules locaux vers GitHub.

Usage:
    python manage.py update_modules_online --owner=username --branch=main
    python manage.py update_modules_online --owner=username --branch=main --dry-run
    python manage.py update_modules_online --owner=username --branch=main --force-push
    python manage.py update_modules_online --owner=username --branch=main --modules=claim policy
"""

import os
import subprocess
import sys
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Met à jour automatiquement les modules locaux vers GitHub'

    def add_arguments(self, parser):
        parser.add_argument(
            '--owner',
            type=str,
            required=True,
            help='Nom du propriétaire GitHub (ex: username)'
        )
        parser.add_argument(
            '--branch',
            type=str,
            required=True,
            help='Branche cible (ex: main, release/25.04)'
        )
        parser.add_argument(
            '--message',
            type=str,
            default='Auto-update modules from local development',
            help='Message de commit personnalisé'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les actions sans les exécuter'
        )
        parser.add_argument(
            '--force-push',
            action='store_true',
            help='Force le push même si l\'historique diverge'
        )
        parser.add_argument(
            '--modules',
            type=str,
            nargs='*',
            help='Liste des modules spécifiques à mettre à jour (optionnel)'
        )
        parser.add_argument(
            '--skip-dirty',
            action='store_true',
            help='Ignore les modules avec des modifications non commitées'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affichage détaillé des opérations'
        )
        parser.add_argument(
            '--force-push-always',
            action='store_true',
            help='Force le push même sans changement détecté'
        )
        parser.add_argument(
            '--create-branch-if-missing',
            action='store_true',
            default=True,
            help='Créer automatiquement la branche si elle n\'existe pas (défaut: True)'
        )

    def handle(self, *args, **options):
        self.owner = options['owner']
        self.branch = options['branch']
        self.message = options['message']
        self.dry_run = options['dry_run']
        self.force_push = options['force_push']
        self.target_modules = options['modules']
        self.skip_dirty = options['skip_dirty']
        self.verbose = options['verbose']
        self.force_push_always = options['force_push_always']
        self.create_branch_if_missing = options['create_branch_if_missing']

        # Chemin vers le dossier src
        self.src_path = Path(__file__).resolve().parent.parent.parent.parent.parent / 'src'
        
        if not self.src_path.exists():
            raise CommandError(f"Le dossier src n'existe pas: {self.src_path}")

        self.stdout.write(
            self.style.SUCCESS(f"🚀 Mise à jour des modules vers GitHub")
        )
        self.stdout.write(f"📍 Propriétaire: {self.owner}")
        self.stdout.write(f"🌿 Branche: {self.branch}")
        self.stdout.write(f"📝 Message: {self.message}")
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING("🧪 MODE DRY-RUN - Aucune modification ne sera effectuée"))

        # Découvrir les modules
        modules = self.discover_modules()
        
        if self.target_modules:
            modules = [m for m in modules if m.name in self.target_modules]
            if not modules:
                raise CommandError(f"Aucun module trouvé parmi: {self.target_modules}")

        self.stdout.write(f"\n📦 {len(modules)} modules trouvés:")
        for module in modules:
            self.stdout.write(f"   • {module.name}")

        # Traiter chaque module
        success_count = 0
        error_count = 0

        for module in modules:
            try:
                if self.update_module(module):
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Erreur avec {module.name}: {e}")
                )
                error_count += 1

        # Résumé final
        self.stdout.write(f"\n📊 Résumé:")
        self.stdout.write(self.style.SUCCESS(f"   ✅ Succès: {success_count}"))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"   ❌ Erreurs: {error_count}"))

    def load_openimis_config(self):
        """Charge la configuration depuis openimis.json"""
        config_path = Path(__file__).resolve().parent.parent.parent.parent.parent / 'openimis.json'
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                self.stdout.write(self.style.WARNING(f"⚠️  Impossible de lire openimis.json: {e}"))
        return {}

    def discover_modules(self):
        """Découvre tous les modules dans le dossier src"""
        modules = []
        config = self.load_openimis_config()
        
        # Créer un mapping des modules depuis openimis.json
        module_mapping = {}
        if 'modules' in config:
            for module_config in config['modules']:
                name = module_config.get('name', '')
                pip_url = module_config.get('pip', '')
                
                # Extraire le nom du repo depuis l'URL pip
                # Format: git+https://github.com/sackofils/openimis-be-location_py.git@release/25.04#egg=openimis-be-location
                if 'github.com' in pip_url:
                    try:
                        # Extraire le nom du repo
                        repo_part = pip_url.split('github.com/')[1].split('.git')[0]
                        owner_part, repo_name = repo_part.split('/', 1)
                        
                        # Le nom du dossier est openimis-be-{name}
                        # Le mapping est: nom_dossier -> nom_repo_github
                        module_key = f"openimis-be-{name}"
                        module_mapping[module_key] = repo_name
                    except (IndexError, ValueError):
                        pass
        
        # Parcourir TOUS les modules dans src/, pas seulement ceux de openimis.json
        all_items = list(self.src_path.iterdir())
        if self.verbose:
            self.stdout.write(f"   🔍 {len(all_items)} éléments trouvés dans {self.src_path}")
        
        for item in all_items:
            if item.is_dir() and item.name.startswith('openimis-be-'):
                # Le nom du dossier (ex: openimis-be-location)
                folder_name = item.name
                
                # Extraire le nom du module pour l'affichage (ex: location)
                module_name = folder_name.replace('openimis-be-', '').replace('_', '-')
                
                # Utiliser le mapping depuis openimis.json si disponible, sinon générer automatiquement
                if folder_name in module_mapping:
                    repo_name = module_mapping[folder_name]
                    if self.verbose:
                        self.stdout.write(f"   📋 {folder_name} -> {repo_name} (depuis openimis.json)")
                else:
                    # Générer le nom du repo automatiquement
                    # Format: openimis-be-{name}_py où {name} utilise des underscores
                    # Convertir les tirets en underscores dans le nom du module
                    if folder_name.endswith('_py'):
                        repo_name = folder_name
                    else:
                        # Convertir openimis-be-api-etl -> openimis-be-api_etl_py
                        # Garder openimis-be- au début, convertir le reste en underscores
                        module_part = folder_name.replace('openimis-be-', '')
                        # Gérer le cas spécial kobo-connect-py (éviter double _py)
                        if module_part.endswith('-py'):
                            module_part = module_part.replace('-py', '')
                        repo_name = f"openimis-be-{module_part.replace('-', '_')}_py"
                    if self.verbose:
                        self.stdout.write(f"   🔧 {folder_name} -> {repo_name} (généré automatiquement)")
                
                modules.append(ModuleInfo(
                    name=module_name,
                    path=item,
                    repo_name=repo_name,
                    remote_url=f"https://github.com/{self.owner}/{repo_name}.git"
                ))
        
        return sorted(modules, key=lambda x: x.name)

    def update_module(self, module):
        """Met à jour un module spécifique"""
        self.stdout.write(f"\n🔄 Traitement de {module.name}...")
        
        try:
            # Vérifier si le dossier est un repo git
            if not (module.path / '.git').exists():
                self.stdout.write(
                    self.style.WARNING(f"   ⚠️  {module.name} n'est pas un repo git, ignoré")
                )
                return False

            # Vérifier l'état du repo
            if not self.skip_dirty and self.is_repo_dirty(module.path):
                self.stdout.write(
                    self.style.WARNING(f"   ⚠️  {module.name} a des modifications non commitées, ignoré")
                )
                return False
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Erreur lors de la vérification: {e}")
            )
            return False

        try:
            # Vérifier et configurer le remote
            if not self.configure_remote(module):
                return False

            # Ajouter tous les fichiers
            if not self.dry_run:
                self.git_command(module.path, ['add', '.'])
                self.stdout.write(f"   📝 Fichiers ajoutés")

            # Vérifier s'il y a des changements à commiter
            if self.has_changes_to_commit(module.path):
                if not self.dry_run:
                    # Commit avec le message
                    self.git_command(module.path, ['commit', '-m', self.message])
                    self.stdout.write(f"   💾 Commit effectué: {self.message}")
                else:
                    self.stdout.write(f"   💾 Commit à effectuer: {self.message}")

                # Push vers GitHub
                if not self.dry_run:
                    if self.force_push or self.force_push_always:
                        self.git_command(module.path, ['push', 'origin', self.branch, '--force-with-lease'])
                        self.stdout.write(f"   🚀 Push forcé avec lease vers origin/{self.branch}")
                    else:
                        self.git_command(module.path, ['push', 'origin', self.branch])
                        self.stdout.write(f"   🚀 Push vers origin/{self.branch}")
                else:
                    self.stdout.write(f"   🚀 Push à effectuer vers origin/{self.branch}")
            else:
                self.stdout.write(f"   ℹ️  Aucun changement à commiter")
                # Push quand même (par défaut)
                if not self.dry_run:
                    if self.force_push or self.force_push_always:
                        self.git_command(module.path, ['push', 'origin', self.branch, '--force-with-lease'])
                        self.stdout.write(f"   🚀 Push forcé avec lease vers origin/{self.branch} (aucun changement détecté)")
                    else:
                        self.git_command(module.path, ['push', 'origin', self.branch])
                        self.stdout.write(f"   🚀 Push vers origin/{self.branch} (aucun changement détecté)")
                else:
                    if self.force_push or self.force_push_always:
                        self.stdout.write(f"   🚀 Push forcé avec lease à effectuer vers origin/{self.branch} (aucun changement détecté)")
                    else:
                        self.stdout.write(f"   🚀 Push à effectuer vers origin/{self.branch} (aucun changement détecté)")

            return True

        except subprocess.CalledProcessError as e:
            if hasattr(e.stderr, 'decode'):
                error_msg = e.stderr.decode()
            elif isinstance(e.stderr, str):
                error_msg = e.stderr
            else:
                error_msg = str(e.stderr)
            self.stdout.write(
                self.style.ERROR(f"   ❌ Erreur git: {error_msg}")
            )
            return False

    def configure_remote(self, module):
        """Configure le remote origin pour pointer vers le bon repo"""
        try:
            # Vérifier le remote actuel
            result = self.git_command(module.path, ['remote', 'get-url', 'origin'], capture=True)
            current_url = result.stdout.strip()
            
            if current_url != module.remote_url:
                if not self.dry_run:
                    self.git_command(module.path, ['remote', 'set-url', 'origin', module.remote_url])
                    self.stdout.write(f"   🔗 Remote configuré: {module.remote_url}")
                else:
                    self.stdout.write(f"   🔗 Remote à configurer: {module.remote_url}")
            else:
                self.stdout.write(f"   ✅ Remote déjà configuré")

            # Vérifier si la branche existe localement
            try:
                self.git_command(module.path, ['rev-parse', '--verify', self.branch], capture=True)
                branch_exists_locally = True
            except subprocess.CalledProcessError:
                branch_exists_locally = False

            # Vérifier si la branche existe sur GitHub
            try:
                self.git_command(module.path, ['ls-remote', '--heads', 'origin', self.branch], capture=True)
                branch_exists_remote = True
            except subprocess.CalledProcessError:
                branch_exists_remote = False

            if self.create_branch_if_missing:
                if not branch_exists_locally and not branch_exists_remote:
                    # Créer la branche localement et la pousser vers GitHub
                    if not self.dry_run:
                        # Créer la branche localement
                        self.git_command(module.path, ['checkout', '-b', self.branch])
                        # Pousser la nouvelle branche vers GitHub
                        self.git_command(module.path, ['push', '-u', 'origin', self.branch])
                        self.stdout.write(f"   🌿 Branche {self.branch} créée localement et poussée vers GitHub")
                    else:
                        self.stdout.write(f"   🌿 Branche {self.branch} à créer localement et pousser vers GitHub")
                elif not branch_exists_locally and branch_exists_remote:
                    # La branche existe sur GitHub mais pas localement, la récupérer
                    if not self.dry_run:
                        self.git_command(module.path, ['checkout', '-b', self.branch, f'origin/{self.branch}'])
                        self.stdout.write(f"   🌿 Branche {self.branch} récupérée depuis GitHub")
                    else:
                        self.stdout.write(f"   🌿 Branche {self.branch} à récupérer depuis GitHub")
                elif branch_exists_locally and not branch_exists_remote:
                    # La branche existe localement mais pas sur GitHub, la pousser
                    if not self.dry_run:
                        self.git_command(module.path, ['push', '-u', 'origin', self.branch])
                        self.stdout.write(f"   🌿 Branche {self.branch} poussée vers GitHub")
                    else:
                        self.stdout.write(f"   🌿 Branche {self.branch} à pousser vers GitHub")
                else:
                    # La branche existe partout
                    self.stdout.write(f"   ✅ Branche {self.branch} existe déjà")
            else:
                # Vérifier que la branche existe, sinon erreur
                if not branch_exists_locally:
                    raise CommandError(f"Branche {self.branch} n'existe pas localement et création automatique désactivée")
                self.stdout.write(f"   ✅ Branche {self.branch} existe localement")

            return True

        except subprocess.CalledProcessError as e:
            if hasattr(e.stderr, 'decode'):
                error_msg = e.stderr.decode()
            elif isinstance(e.stderr, str):
                error_msg = e.stderr
            else:
                error_msg = str(e.stderr)
            self.stdout.write(
                self.style.ERROR(f"   ❌ Erreur de configuration remote: {error_msg}")
            )
            return False

    def is_repo_dirty(self, repo_path):
        """Vérifie si le repo a des modifications non commitées"""
        try:
            result = self.git_command(repo_path, ['status', '--porcelain'], capture=True)
            return bool(result.stdout.strip())
        except subprocess.CalledProcessError:
            return True

    def has_changes_to_commit(self, repo_path):
        """Vérifie s'il y a des changements à commiter"""
        try:
            self.git_command(repo_path, ['diff', '--staged', '--quiet'], capture=True)
            return False  # Si la commande réussit, il n'y a pas de changements
        except subprocess.CalledProcessError:
            return True  # Si la commande échoue, il y a des changements

    def git_command(self, repo_path, args, capture=False):
        """Exécute une commande git dans le repo spécifié"""
        cmd = ['git'] + args
        if self.verbose:
            self.stdout.write(f"   🔧 Exécution: {' '.join(cmd)}")
        
        try:
            if capture:
                return subprocess.run(
                    cmd,
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
            else:
                result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
                if result.returncode != 0:
                    # Créer une exception avec les bonnes informations
                    exc = subprocess.CalledProcessError(result.returncode, cmd)
                    exc.stdout = result.stdout
                    exc.stderr = result.stderr
                    raise exc
                return result
        except subprocess.CalledProcessError as e:
            # S'assurer que stderr est une chaîne
            if not isinstance(e.stderr, str):
                e.stderr = str(e.stderr)
            raise e


class ModuleInfo:
    """Classe pour représenter les informations d'un module"""
    def __init__(self, name, path, repo_name, remote_url):
        self.name = name
        self.path = path
        self.repo_name = repo_name
        self.remote_url = remote_url



# auto abdoullatif main
#python manage.py update_modules_online --owner=abdoullatif --branch=main --create-branch-if-missing --no-create-branch-if-missing

#python manage.py update_modules_online --owner=abdoullatif --branch=release/25.04

# auto abdoullatif release/25.04
#python manage.py update_modules_online --owner=abdoullatif --branch=release/25.04

# auto abdoullatif main --dry-run
#python manage.py update_modules_online --owner=abdoullatif --branch=main --dry-run --verbose

# auto abdoullatif release/25.04 --dry-run

# RESTE A PUSHER ----  contribution plan / claim / core / grivance social protection / Kobo connect / product / 

