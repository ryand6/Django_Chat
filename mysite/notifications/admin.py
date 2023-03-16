from django.contrib import admin
from django.core.paginator import Paginator
from django.core.cache import cache
from notifications.models import Notifications


# Source: http://masnun.rocks/2017/03/20/django-admin-expensive-count-all-queries/
# Used to cache results of expensive database query in admin site so that expensive query is only run once and then retrieves cached results in future
class CachingPaginator(Paginator):
    def _get_count(self):

        if not hasattr(self, "_count"):
            self._count = None

        if self._count is None:
            try:
                key = "adm:{0}:count".format(hash(self.object_list.query.__str__()))
                self._count = cache.get(key, -1)
                if self._count == -1:
                    self._count = super().count
                    cache.set(key, self._count, 3600)

            except:
                self._count = len(self.object_list)
        return self._count

    count = property(_get_count)


class NotificationsAdmin(admin.ModelAdmin):
    list_filter = ['recipient', 'sender', 'read', 'timestamp']
    list_display = ['recipient', 'sender', 'message', 'timestamp', 'read']
    search_fields = ['recipient__username', 'sender__username']
    readonly_fields = ['id', 'recipient', 'sender', 'link_id', 'timestamp']

    # prevent duplicated SELECT COUNT(*) query being run (expensive query on large datasets)
    show_full_result_count = False
    # call caching system to retrieve cached results if they exist already
    paginator = CachingPaginator


admin.site.register(Notifications, NotificationsAdmin)