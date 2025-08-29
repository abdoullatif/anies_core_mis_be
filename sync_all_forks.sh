#!/bin/bash

# Usage : ./sync_forks_from_json.sh modules.json [branche] [chemin] [username] [token]

JSON_FILE=$1
BRANCH=${2:-develop}
REPO_BASE_PATH=${3:-$(pwd)}
GITHUB_USERNAME=$4
GITHUB_TOKEN=$5

if [ ! -f "$JSON_FILE" ]; then
  echo "Fichier JSON introuvable : $JSON_FILE"
  exit 1
fi

if [[ -z "$GITHUB_USERNAME" || -z "$GITHUB_TOKEN" ]]; then
  echo "Nom d'utilisateur ou token manquant. Utilisation :"
  echo "./sync_all_forks.sh modules.json develop /chemin username token"
  exit 1
fi

echo "Fichier JSON : $JSON_FILE"
echo "Branche cible : $BRANCH"
echo "Répertoire des modules : $REPO_BASE_PATH"
echo "Utilisateur GitHub : $GITHUB_USERNAME"
echo "----------------------------------------"

jq -c '.modules[]' "$JSON_FILE" | while read -r module; do
  PIP_URL=$(echo "$module" | jq -r '.pip')

  # Récupère le nom du dossier à partir du egg=
  EGG_NAME=$(echo "$PIP_URL" | grep -oE 'egg=[^&#]+' | cut -d= -f2)

  # URL Git "propre"
  UPSTREAM_URL=$(echo "$PIP_URL" | sed -E 's|git\+([^#@]+)(@[^#]*)?.*|\1|')

  echo "Module : $EGG_NAME"
  echo "Upstream (sans auth) : $UPSTREAM_URL"

  MODULE_PATH="$REPO_BASE_PATH/$EGG_NAME"

  if [ -d "$MODULE_PATH/.git" ]; then
    cd "$MODULE_PATH" || continue

    # Configure upstream sans authentification
    if git remote | grep -q upstream; then
      git remote set-url upstream "$UPSTREAM_URL"
    else
      git remote add upstream "$UPSTREAM_URL"
      echo "Remote 'upstream' ajouté."
    fi

    git fetch upstream

    git checkout "$BRANCH" 2>/dev/null || {
      echo "Branche $BRANCH introuvable. Passage au suivant."
      cd "$REPO_BASE_PATH"
      continue
    }

    echo "Fusion avec upstream/$BRANCH..."
    git merge upstream/"$BRANCH" --no-edit

    # Push avec authentification sur fork (remplace "openimis" par "sackofils")
    ORIGIN_URL=$(git remote get-url origin)

    # Remplacement du owner dans l'URL
    AUTH_ORIGIN_URL=$(echo "$ORIGIN_URL" \
      | sed -E "s|https://|https://$GITHUB_USERNAME:$GITHUB_TOKEN@|" \
      | sed -E "s|github.com/openimis/|github.com/sackofils/|")

    echo "Push sécurisé vers fork : $AUTH_ORIGIN_URL"
    git push "$AUTH_ORIGIN_URL" "$BRANCH"

    cd "$REPO_BASE_PATH" || exit
    echo "Terminé pour $EGG_NAME"
    echo "----------------------------------------"
  else
    echo "'$MODULE_PATH' n'est pas un dépôt Git"
    echo "----------------------------------------"
  fi
done

echo "Synchronisation terminée pour tous les modules."

# ./sync_all_forks.sh ./modules.json release/25.04 ../src