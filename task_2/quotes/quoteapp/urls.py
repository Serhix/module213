from django.urls import path
from . import views
from .apps import QuoteappConfig

app_name = QuoteappConfig.name

urlpatterns = [
    path('', views.main, name='main'),
    path('tag/', views.tag, name='tag'),
    path('author/', views.author, name='author'),
    path('quote/', views.quote, name='quote'),
    path('scraper/', views.start_scraping, name='start_scraping'),
    path('about/<int:author_id>', views.about_author, name='about_author'),
    path('quotes_by_tag/<str:tag_name>', views.quotes_by_tag, name='quotes_by_tag'),

]
