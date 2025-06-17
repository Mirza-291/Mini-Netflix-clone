from django.urls import path, include
from . import views

urlpatterns = [
# Landing Page
path('', views.index, name='index'),
#login
path('login', views.user_login, name='login'),
#signup
path('signup', views.user_signup, name='signup'),
#logout
path('logout', views.user_logout, name='logout'),
#homepage
path('home', views.home, name='home'),
#Semantic Search
path('search', views.search, name='search'),
path("search_page",       views.search_page, name="search_page"),

# browse movies
path('movies', views.movies, name='movies'),
# browse tv shows
path('tvshows', views.tvshows, name='tvshows'),
#browse by language 
path('browsebylanguage', views.browsebylanguage, name='browsebylanguage'),
# mylist
path('add_to_list/', views.add_to_list, name='add_to_list'),
# watched
path('mark_watched', views.mark_watched, name='mark_watched'),
# watched
path('mylist', views.mylist, name='mylist'),
# remove froom mylist
 path("mylist/remove/", views.remove_from_list, name="remove_from_list"),
# trending
path('new-and-popular', views.new_popular, name='new_popular'),
# Multi query
path('multiquery', views.multi_query, name='multiquery'),
#profile
path("profile/password/", views.change_password, name="change_password"),
path("profile/delete/",   views.delete_account, name="delete_account"),
#visualization
path("visualization/", views.visualization, name="visualization"),
# details api
path("detail-api/<str:title>/", views.detail_api, name="detail_api"),




# crud
path('crud', views.crud, name='crud'),
path('api/<str:coll>/', views.crud_list,   name='crud_list'),
path('api/<str:coll>/<str:pk>/', views.crud_detail, name='crud_detail'),


# admin auth
    path("administrator/login/",               views.admin_login,     name="admin_login"),
    path("administrator/logout/",              views.admin_logout,    name="admin_logout"),

    # admin dashboard (with optional section)
    path("administrator/",                     views.admin_dashboard, name="admin_dashboard"),
    path("administrator/<str:section>/",       views.admin_dashboard, name="admin_dashboard"),

    # administrator operations for movies
    path("administrator/movies/create/",        views.movie_create,     name="movie_create"),
    path("administrator/movies/<str:id>/edit/", views.movie_update,     name="movie_update"),
    path("administrator/movies/<str:id>/delete/", views.movie_delete,   name="movie_delete"),

    # administrator operations for tvshows
    path("administrator/tvshow/create/",       views.tvshow_create,    name="tvshow_create"),
    path("administrator/tvshow/<str:id>/edit/",views.tvshow_update,    name="tvshow_update"),
    path("administrator/tvshow/<str:id>/delete/", views.tvshow_delete,  name="tvshow_delete"),

    # administrator operations for users
    path("administrator/users/create/",         views.user_create,      name="user_create"),
    path("administrator/users/<str:id>/edit/",  views.user_update,      name="user_update"),
    path("administrator/users/<str:id>/delete/",views.user_delete,      name="user_delete"),


]


from django.conf     import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )