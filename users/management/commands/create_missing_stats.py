from django.core.management.base import BaseCommand
from users.models import Profile, CompletionStats

class Command(BaseCommand):
    help = 'Create missing CompletionStats for existing profiles'

    def handle(self, *args, **options):
        profiles = Profile.objects.all()
        created_count = 0
        
        for profile in profiles:
            stats, created = CompletionStats.objects.get_or_create(profile=profile)
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created CompletionStats for profile: {profile}'
                    )
                )
        
        if created_count == 0:
            self.stdout.write(
                self.style.SUCCESS('All profiles already have CompletionStats')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {created_count} CompletionStats'
                )
            ) 