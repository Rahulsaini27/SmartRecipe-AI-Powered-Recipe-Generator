

from django.contrib import admin
from django.urls import path
from .views import home, signup, user_login, user_logout, recipehistory ,generate_recipes

urlpatterns = [
   
     path('', home, name='home'),
    path('signup/', signup, name='signup'),
    path('login/', user_login, name='login'),
    path('generate-recipes/', generate_recipes, name='generate-recipes'),
    path('recipehistory/', recipehistory, name='recipehistory'),
    path('admin/', admin.site.urls),
    path('logout/', user_logout, name='logout'),
]

