# your_project_name/urls.py

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from .schema import schema  # Your GraphQL schema
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # GraphQL endpoint with CSRF disabled (for development or if using token auth)
    path("graphql/", csrf_exempt(GraphQLView.as_view(graphiql=True, schema=schema))),
    path("payment/", include("payment.urls")),

]

# Serve media files in development (e.g., images uploaded to MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
