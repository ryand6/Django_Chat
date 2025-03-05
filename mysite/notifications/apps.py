from django.apps import AppConfig
import atexit

class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'

    def ready(self):
        import notifications.signals
        atexit.register(self.reset_user_statuses_on_shutdown)

    def reset_user_statuses_on_shutdown(self):
        from account.models import Account
        # This method will be called when the server shuts down
        users = Account.objects.all()
        for user in users:
            user.online_status = 'offline'
            user.save()
        print("Successfully reset all users' statuses to offline.")