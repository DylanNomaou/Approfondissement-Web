"""
Commande Django pour nettoyer automatiquement les codes de réinitialisation expirés.
Usage: python manage.py cleanup_expired_codes
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from restoplus.models import PasswordResetCode


class Command(BaseCommand):
    help = 'Nettoie les codes de réinitialisation de mot de passe expirés'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche combien de codes seraient supprimés sans les supprimer',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=0,
            help='Supprimer les codes expirés depuis X jours (défaut: 0 = seulement les expirés)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        extra_days = options['days']
        
        # Calculer la date limite
        if extra_days > 0:
            cutoff_date = timezone.now() - timezone.timedelta(days=extra_days)
            queryset = PasswordResetCode.objects.filter(expires_at__lt=cutoff_date)
            self.stdout.write(
                f"Recherche des codes expirés depuis plus de {extra_days} jour(s)..."
            )
        else:
            queryset = PasswordResetCode.objects.filter(expires_at__lt=timezone.now())
            self.stdout.write("Recherche des codes expirés...")
        
        # Compter les codes à supprimer
        count = queryset.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS("Aucun code expiré trouvé. Base de données propre.")
            )
            return
        
        # Afficher les détails
        self.stdout.write(f"Codes expirés trouvés: {count}")
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] {count} code(s) seraient supprimé(s) (utiliser sans --dry-run pour supprimer réellement)"
                )
            )
            
            # Afficher quelques exemples
            examples = queryset[:5]
            if examples:
                self.stdout.write("\nExemples de codes qui seraient supprimés:")
                for code in examples:
                    self.stdout.write(
                        f"  - {code.email} | {code.code} | expiré le {code.expires_at.strftime('%Y-%m-%d %H:%M')}"
                    )
                if count > 5:
                    self.stdout.write(f"  ... et {count - 5} autres")
        else:
            # Supprimer réellement
            deleted_count, details = queryset.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Suppression terminée: {deleted_count} code(s) expiré(s) supprimé(s)"
                )
            )
            
            # Afficher les détails de suppression
            if details:
                self.stdout.write("\nDétails de la suppression:")
                for model, count in details.items():
                    if count > 0:
                        self.stdout.write(f"  - {model}: {count} enregistrement(s)")
        
        # Statistiques générales
        total_codes = PasswordResetCode.objects.count()
        active_codes = PasswordResetCode.objects.filter(
            expires_at__gt=timezone.now(),
            is_used=False
        ).count()
        
        self.stdout.write(f"\nStatistiques actuelles:")
        self.stdout.write(f"  - Total codes en base: {total_codes}")
        self.stdout.write(f"  - Codes actifs: {active_codes}")
        self.stdout.write(f"  - Codes inactifs/expirés: {total_codes - active_codes}")
        
        if not dry_run and count > 0:
            self.stdout.write(
                self.style.SUCCESS("\n✨ Nettoyage terminé avec succès!")
            )