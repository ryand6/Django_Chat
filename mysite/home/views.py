# from django.shortcuts import render
# from django.conf import settings
from better_profanity import profanity
    

# class HomeView(View):
#     def get(self, request):
#         host = request.get_host()
#         islocal = host.find('localhost') >= 0 or host.find('127.0.0.1') >= 0
#         context = {
#             'installed': settings.INSTALLED_APPS,
#             'islocal': islocal
#         }
#         return render(request, 'home/main.html', context)


def sanitise_text(text):
    if profanity.contains_profanity(text):
        return profanity.censor(text)
    else:
        return text