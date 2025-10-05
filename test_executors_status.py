#!/usr/bin/env python3
"""
Script de test pour vérifier la nouvelle fonctionnalité executors_status
"""

import os
import sys
import django

# Configuration Django
sys.path.append('/openimis-be/openIMIS')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'openIMIS.settings')
django.setup()

from tasks_management.models import Task, TaskGroup, TaskExecutor
from core.models import User
from django.contrib.contenttypes.models import ContentType

def test_executors_status():
    """Test de la fonctionnalité executors_status"""
    
    print("🔍 Test de la fonctionnalité executors_status")
    print("=" * 50)
    
    # Vérifier s'il y a des tâches dans la base de données
    tasks = Task.objects.select_related('task_group').prefetch_related(
        'task_group__taskexecutor_set__user__i_user'
    ).filter(is_deleted=False)[:5]
    
    if not tasks:
        print("❌ Aucune tâche trouvée dans la base de données")
        return
    
    print(f"✅ {tasks.count()} tâches trouvées")
    
    for i, task in enumerate(tasks, 1):
        print(f"\n📋 Tâche {i}: {task.source}")
        print(f"   UUID: {task.uuid}")
        print(f"   Statut: {task.status}")
        print(f"   Groupe: {task.task_group.code if task.task_group else 'Aucun'}")
        
        if task.task_group:
            # Simuler la logique de resolve_executors_status
            executors = task.task_group.taskexecutor_set.filter(is_deleted=False).select_related('user', 'user__i_user')
            print(f"   Exécuteurs assignés: {executors.count()}")
            
            for executor in executors:
                user = executor.user
                user_id = str(user.id)
                business_status = task.business_status or {}
                user_status = business_status.get(user_id, "PENDING")
                
                # Construire le nom complet
                full_name = user.login_name
                if hasattr(user, 'i_user') and user.i_user:
                    i_user = user.i_user
                    parts = []
                    if hasattr(i_user, 'other_names') and i_user.other_names:
                        parts.append(i_user.other_names)
                    if hasattr(i_user, 'last_name') and i_user.last_name:
                        parts.append(i_user.last_name)
                    if parts:
                        full_name = " ".join(parts)
                
                status_display = {
                    "APPROVED": "✅ Tâche validée",
                    "PENDING": "⏳ En attente de validation",
                    "REJECTED": "❌ Tâche rejetée",
                    "FAILED": "💥 Échec de validation"
                }.get(user_status, "⏳ En attente de validation")
                
                print(f"     👤 {full_name} ({user.login_name}): {status_display}")
        else:
            print("   ⚠️  Aucun groupe de tâches assigné")
    
    print("\n" + "=" * 50)
    print("✅ Test terminé avec succès !")

if __name__ == "__main__":
    test_executors_status()

