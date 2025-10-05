# 🚀 Exemples d'utilisation de la commande Django

## 📋 Commande principale

```bash
cd openIMIS && python manage.py update_modules_online --owner=abdoullatif --branch=release/25.04
```

## 🎯 Exemples d'utilisation

### 1. Test avec dry-run (recommandé en premier)
```bash
python manage.py update_modules_online --owner=abdoullatif --branch=release/25.04 --dry-run
```

### 2. Mise à jour réelle de tous les modules
```bash
python manage.py update_modules_online --owner=abdoullatif --branch=release/25.04
```

### 3. Push forcé même sans changement
```bash
python manage.py update_modules_online --owner=abdoullatif --branch=release/25.04 --force-push-always
```

### 4. Modules spécifiques seulement
```bash
python manage.py update_modules_online --owner=abdoullatif --branch=release/25.04 --modules core claim policy
```

### 5. Avec message personnalisé
```bash
python manage.py update_modules_online --owner=abdoullatif --branch=release/25.04 --message="Update from dev environment"
```

### 6. Mode verbose pour plus de détails
```bash
python manage.py update_modules_online --owner=abdoullatif --branch=release/25.04 --verbose
```

### 7. Ignorer les modules avec modifications non commitées
```bash
python manage.py update_modules_online --owner=abdoullatif --branch=release/25.04 --skip-dirty
```

### 8. Force push si historique diverge
```bash
python manage.py update_modules_online --owner=abdoullatif --branch=release/25.04 --force-push
```

### 9. Créer automatiquement les branches manquantes
```bash
python manage.py update_modules_online --owner=abdoullatif --branch=ma-nouvelle-branche --create-branch-if-missing
```

## 🔧 Paramètres disponibles

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| `--owner` | **Requis** - Nom d'utilisateur GitHub | `--owner=abdoullatif` |
| `--branch` | **Requis** - Branche cible | `--branch=release/25.04` |
| `--message` | Message de commit | `--message="Update modules"` |
| `--dry-run` | Test sans modifications | `--dry-run` |
| `--force-push` | Force push si divergence | `--force-push` |
| `--force-push-always` | Push même sans changement | `--force-push-always` |
| `--modules` | Modules spécifiques | `--modules core claim` |
| `--skip-dirty` | Ignorer repos sales | `--skip-dirty` |
| `--verbose` | Affichage détaillé | `--verbose` |
| `--create-branch-if-missing` | Créer branche si manquante | `--create-branch-if-missing` |

## 🎯 Cas d'usage typiques

### Développement local
```bash
python manage.py update_modules_online --owner=abdoullatif --branch=main --message="Dev updates"
```

### Production
```bash
python manage.py update_modules_online --owner=abdoullatif --branch=release/25.04 --force-push-always
```

### Test avant mise à jour
```bash
python manage.py update_modules_online --owner=abdoullatif --branch=release/25.04 --dry-run --verbose
```

### Créer une nouvelle branche pour tous les modules
```bash
python manage.py update_modules_online --owner=abdoullatif --branch=feature/nouvelle-fonctionnalite --create-branch-if-missing
```

## ✅ Fonctionnalités

- ✅ **Découverte automatique** des modules depuis `openimis.json`
- ✅ **Mapping automatique** des noms de repos GitHub
- ✅ **Configuration automatique** des remotes
- ✅ **Push sécurisé** avec `--force-with-lease`
- ✅ **Gestion des erreurs** robuste
- ✅ **Mode dry-run** pour tester
- ✅ **Modules spécifiques** ou tous les modules
- ✅ **Aucun fichier de config** externe nécessaire
- ✅ **Création automatique** des branches manquantes (avec `--create-branch-if-missing`)
