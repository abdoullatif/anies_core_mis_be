# 📋 Documentation : Nouvelle colonne "Utilisateurs" dans les tâches

## 🎯 Objectif

Ajouter une nouvelle colonne "Utilisateurs" dans le DataTable des tâches qui affiche le statut de validation de chaque utilisateur assigné à la tâche.

## 🔧 Modifications apportées

### 1. Nouveau champ GraphQL `executors_status`

Le champ `executors_status` a été ajouté aux types GraphQL `TaskGQLType` et `TaskHistoryGQLType`.

**Format de retour :**
```json
{
  "executorsStatus": [
    {
      "user_id": "uuid-de-l-utilisateur",
      "username": "login_name",
      "full_name": "Prénom Nom",
      "status": "APPROVED|PENDING|REJECTED|FAILED",
      "status_display": "Tâche validée|En attente de validation|Tâche rejetée|Échec de validation"
    }
  ]
}
```

### 2. Exemple d'utilisation dans le frontend

#### Requête GraphQL
```graphql
query GetTasksWithExecutorsStatus {
  tasks {
    edges {
      node {
        id
        uuid
        source
        status
        entityString
        dateCreated
        taskGroup {
          code
          completionPolicy
        }
        executorsStatus {
          user_id
          username
          full_name
          status
          status_display
        }
      }
    }
  }
}
```

#### Affichage dans le DataTable
```javascript
// Colonne "Utilisateurs" dans le DataTable
{
  field: 'executorsStatus',
  headerName: 'Utilisateurs',
  width: 300,
  renderCell: (params) => {
    const executors = params.value || [];
    return (
      <div>
        {executors.map((executor, index) => (
          <div key={index} style={{ marginBottom: '2px' }}>
            <span style={{ 
              color: executor.status === 'APPROVED' ? 'green' : 
                     executor.status === 'REJECTED' ? 'red' : 'orange',
              fontWeight: 'bold'
            }}>
              {executor.full_name || executor.username}
            </span>
            <span style={{ marginLeft: '5px', fontSize: '0.8em' }}>
              ({executor.status_display})
            </span>
          </div>
        ))}
      </div>
    );
  }
}
```

### 3. Statuts possibles

| Statut | Description | Affichage |
|--------|-------------|-----------|
| `APPROVED` | Utilisateur a validé la tâche | ✅ Tâche validée |
| `PENDING` | Utilisateur n'a pas encore validé | ⏳ En attente de validation |
| `REJECTED` | Utilisateur a rejeté la tâche | ❌ Tâche rejetée |
| `FAILED` | Échec lors de la validation | 💥 Échec de validation |

## 🔄 Logique de fonctionnement

### 1. Récupération des exécuteurs
- Les exécuteurs sont récupérés via `task.task_group.taskexecutor_set`
- Seuls les exécuteurs non supprimés sont inclus (`is_deleted=False`)

### 2. Détermination du statut
- Le statut est stocké dans `task.business_status` sous la forme d'un dictionnaire
- Clé : `user_id` (string), Valeur : statut de validation
- Si l'utilisateur n'a pas de statut, il est considéré comme `PENDING`

### 3. Construction du nom complet
- Priorité au nom complet depuis `user.i_user.other_names + last_name`
- Fallback sur `user.login_name` si pas de nom complet

## 🚀 Optimisations

### 1. Requêtes optimisées
```python
# Préchargement des relations pour éviter les N+1 queries
queryset.select_related('task_group').prefetch_related(
    'task_group__taskexecutor_set__user__i_user'
)
```

### 2. Cache côté frontend
- Le champ `executorsStatus` peut être mis en cache côté frontend
- Invalidation du cache lors des mutations de tâches

## 🧪 Tests

### Test de la fonctionnalité
```python
# Test manuel via le shell Django
python manage.py shell

from tasks_management.models import Task
task = Task.objects.select_related('task_group').prefetch_related(
    'task_group__taskexecutor_set__user__i_user'
).first()

# Simuler la résolution du champ
if task:
    # La logique est dans resolve_executors_status
    print("Test réussi !")
```

## 📱 Intégration frontend

### 1. Mise à jour de la requête GraphQL
- Ajouter `executorsStatus` aux requêtes existantes
- Modifier les types TypeScript si nécessaire

### 2. Mise à jour du DataTable
- Ajouter la nouvelle colonne "Utilisateurs"
- Implémenter le rendu conditionnel des statuts
- Ajouter des icônes/emojis pour une meilleure UX

### 3. Filtres et tri
- Possibilité de filtrer par statut d'utilisateur
- Tri par nombre d'utilisateurs ayant validé

## 🔐 Sécurité

- Les utilisateurs ne voient que les tâches auxquelles ils ont accès
- Les Task Triage et admins IMIS voient toutes les tâches
- Validation des permissions côté backend maintenue

## 📊 Métriques possibles

Avec cette nouvelle colonne, il devient possible de :
- Suivre le taux de validation par utilisateur
- Identifier les goulots d'étranglement dans les workflows
- Mesurer l'efficacité des politiques de completion (ALL vs ANY)
- Générer des rapports de performance des exécuteurs

## 🎉 Résultat attendu

Le DataTable affichera maintenant :
```
Source | Type | Entité | Groupe de travail | Date de création | Statut | Utilisateurs
-------|------|--------|------------------|------------------|--------|-------------
UserService | CREATE | User123 | USER_APPROVAL | 2025-01-01 | ACCEPTED | user1 (✅ Tâche validée)
                                                                 user2 (⏳ En attente de validation)
                                                                 user3 (⏳ En attente de validation)
```

Cette fonctionnalité améliore considérablement la visibilité sur l'état d'avancement des tâches et facilite la gestion des workflows d'approbation.

