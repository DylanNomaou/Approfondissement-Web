# 🚀 GUIDE DE DÉPLOIEMENT PYTHONANYWHERE - RÉINITIALISATION MOT DE PASSE

## 📋 Prérequis

- [ ] Compte PythonAnywhere configuré
- [ ] Application Django déployée et fonctionnelle
- [ ] Configuration email fonctionnelle (Gmail SMTP)
- [ ] Accès SSH/console à l'environnement

## 🛠️ Étapes de déploiement

### 1. 📁 Upload des fichiers

```bash
# Via l'interface web PythonAnywhere ou via console
# S'assurer que tous ces fichiers sont présents :

# Modèles
restoplus/models.py  # Contient PasswordResetCode

# Vues
restoplus/views.py   # Contient les 4 vues de reset

# URLs
restoplus/urls.py    # Contient les 4 URLs de reset

# Templates
templates/registration/password_reset_request.html
templates/registration/password_reset_verify.html
templates/registration/password_reset_confirm.html
templates/registration/password_reset_complete.html
templates/registration/login.html  # Modifié avec lien "Mot de passe oublié"

# Migrations
restoplus/migrations/0020_passwordresetcode.py

# CSS compilé
restoplus/static/restoplus/css/styles.css  # Contient les nouveaux styles
```

### 2. 🐍 Configuration de l'environnement Python

```bash
# Se connecter à la console PythonAnywhere
# Aller dans le répertoire du projet
cd /home/yourusername/ApprofondissementWeb

# Activer l'environnement virtuel
source .venv/bin/activate  # ou le nom de votre venv

# Vérifier les dépendances (normalement déjà installées)
pip list | grep Django
# Django doit être présent
```

### 3. 📧 Vérification de la configuration email

```python
# Dans la console Django (manage.py shell)
python manage.py shell

# Tester l'envoi d'email
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Test email',
    'Ceci est un test.',
    settings.EMAIL_HOST_USER,
    ['votre-email@test.com'],
    fail_silently=False,
)
# Doit retourner 1 si succès
```

### 4. 🗃️ Migration de la base de données

```bash
# Appliquer les migrations
python manage.py migrate

# Vérifier que la table a été créée
python manage.py shell
>>> from restoplus.models import PasswordResetCode
>>> PasswordResetCode.objects.all()
# Doit retourner une QuerySet vide (pas d'erreur)
```

### 5. 📦 Collecte des fichiers statiques

```bash
# Collecter tous les fichiers statiques
python manage.py collectstatic --noinput

# Les fichiers doivent être copiés dans STATIC_ROOT
# Vérifier que le CSS a été copié correctement
```

### 6. 🌐 Configuration du serveur web

#### A. Via l'interface Web PythonAnywhere

1. **Web tab** > **Static files**
   ```
   URL: /static/
   Directory: /home/yourusername/ApprofondissementWeb/staticfiles
   ```

2. **Web tab** > **Source code**
   ```
   Source code: /home/yourusername/ApprofondissementWeb
   Working directory: /home/yourusername/ApprofondissementWeb
   ```

3. **Web tab** > **WSGI configuration file**
   ```python
   # Vérifier que le path est correct
   path = '/home/yourusername/ApprofondissementWeb'
   if path not in sys.path:
       sys.path.append(path)
   
   os.environ['DJANGO_SETTINGS_MODULE'] = 'ApprofondissementWeb.settings'
   ```

#### B. Mapping des URLs

Les nouvelles URLs seront automatiquement disponibles :
- `/password-reset/` - Demande de réinitialisation
- `/password-reset/verify/` - Saisie du code
- `/password-reset/confirm/` - Nouveau mot de passe
- `/password-reset/complete/` - Confirmation

### 7. 🔄 Redémarrage de l'application

```bash
# Via l'interface web : Web tab > Reload
# Ou via console :
touch /var/www/yourdomain_pythonanywhere_com_wsgi.py
```

### 8. ✅ Tests de validation

#### Tests essentiels en production :

1. **Test de base**
   ```
   URL: https://yourdomain.pythonanywhere.com/login/
   Action: Cliquer sur "Mot de passe oublié ?"
   Attendu: Redirection vers /password-reset/
   ```

2. **Test d'envoi d'email**
   ```
   Action: Saisir un email valide existant
   Attendu: Message de confirmation + email reçu
   ```

3. **Test du flow complet**
   ```
   Action: Compléter tout le processus
   Attendu: Nouveau mot de passe fonctionne
   ```

4. **Test des fichiers statiques**
   ```
   Action: Vérifier le style des pages
   Attendu: CSS appliqué correctement
   ```

## 🛡️ Configuration de sécurité

### 1. Variables d'environnement (Recommandé)

```python
# Dans settings.py, utiliser des variables d'environnement
import os

# Email configuration
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'webproject290@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'euejziymnogbuies')

# Configuration dans PythonAnywhere
# Files tab > .bashrc
export EMAIL_HOST_USER="votre-email@gmail.com"
export EMAIL_HOST_PASSWORD="votre-mot-de-passe-app"
```

### 2. Configuration HTTPS

```python
# En production, s'assurer que settings.py a :
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

### 3. Domaines autorisés

```python
# Ajouter votre domaine PythonAnywhere
ALLOWED_HOSTS = [
    'yourdomain.pythonanywhere.com',
    # ... autres domaines
]

CSRF_TRUSTED_ORIGINS = [
    'https://yourdomain.pythonanywhere.com',
    # ... autres domaines
]
```

## 🔧 Maintenance et monitoring

### 1. Nettoyage automatique

```python
# Créer une tâche cron pour nettoyer les codes expirés
# Console PythonAnywhere > Task tab

# Command:
/home/yourusername/.venv/bin/python /home/yourusername/ApprofondissementWeb/manage.py shell -c "from restoplus.models import PasswordResetCode; PasswordResetCode.cleanup_expired()"

# Hour: 2 (2h du matin)
# Minute: 0
```

### 2. Monitoring des logs

```bash
# Vérifier les logs d'erreur
tail -f /var/log/yourdomain.pythonanywhere.com.error.log

# Vérifier les logs d'accès
tail -f /var/log/yourdomain.pythonanywhere.com.access.log
```

### 3. Sauvegarde

```bash
# Sauvegarder la base de données avant déploiement
python manage.py dumpdata > backup_before_reset_feature.json

# En cas de problème, restaurer :
python manage.py loaddata backup_before_reset_feature.json
```

## 🐛 Résolution de problèmes

### Problème : Emails non reçus
```bash
# Vérifications :
1. Configuration SMTP correcte dans settings.py
2. Mot de passe d'application Gmail valide
3. Firewall PythonAnywhere autorise SMTP
4. Logs d'erreur pour exceptions email
```

### Problème : Erreur 500 sur les pages de reset
```bash
# Vérifications :
1. Migration appliquée : python manage.py showmigrations
2. Fichiers statiques collectés : ls staticfiles/
3. Syntaxe des templates correcte
4. Imports des modèles dans views.py
```

### Problème : CSS ne s'applique pas
```bash
# Vérifications :
1. STATIC_ROOT configuré correctement
2. python manage.py collectstatic exécuté
3. Mapping static files dans Web tab
4. Cache navigateur vidé
```

### Problème : CSRF error
```bash
# Vérifications :
1. CSRF_TRUSTED_ORIGINS inclut votre domaine
2. Formulaires ont {% csrf_token %}
3. HTTPS configuré si en production
```

## ✅ Checklist finale de déploiement

- [ ] **Code uploadé** : Tous les fichiers sur PythonAnywhere
- [ ] **Migration appliquée** : Table PasswordResetCode créée
- [ ] **Fichiers statiques** : CSS compilé et collecté
- [ ] **Configuration email** : SMTP fonctionnel
- [ ] **URLs mappées** : Routes accessibles
- [ ] **WSGI rechargé** : Application redémarrée
- [ ] **Test de base** : Flow complet testé
- [ ] **Sécurité** : HTTPS et CSRF configurés
- [ ] **Monitoring** : Logs vérifiés
- [ ] **Sauvegarde** : Backup créé avant déploiement

## 🎯 URLs finales en production

- **Connexion** : `https://yourdomain.pythonanywhere.com/login/`
- **Reset demande** : `https://yourdomain.pythonanywhere.com/password-reset/`
- **Reset vérification** : `https://yourdomain.pythonanywhere.com/password-reset/verify/`
- **Reset confirmation** : `https://yourdomain.pythonanywhere.com/password-reset/confirm/`
- **Reset terminé** : `https://yourdomain.pythonanywhere.com/password-reset/complete/`

## 📞 Support

En cas de problème pendant le déploiement :
1. Vérifier les logs d'erreur PythonAnywhere
2. Tester chaque composant individuellement
3. Consulter la documentation PythonAnywhere
4. Revenir à la sauvegarde en cas de problème majeur