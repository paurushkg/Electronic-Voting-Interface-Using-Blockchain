from django.contrib import admin
from django.urls import path
from .views  import *


urlpatterns = [
    path('test/', test),
    path('candidate-registration', candidate_registration),
    path('auth-voter', authorize_voter),
    path('go-to-election', go_to_election),
    path('cast-vote', cast_vote),
    path('result', result),
]