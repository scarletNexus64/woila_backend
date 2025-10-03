# EXISTING ENDPOINTS - DO NOT MODIFY URLs - Already integrated in production
# Vehicle management URLs for the Woila VTC platform

from django.urls import path
from . import views

app_name = 'vehicles'

urlpatterns = [
    # EXISTING ENDPOINT: GET /api/vehicles/ - DO NOT MODIFY
    path('', views.VehicleListView.as_view(), name='vehicle-list'),
    
    # EXISTING ENDPOINT: POST /api/vehicles/create/ - DO NOT MODIFY
    path('create/', views.VehicleCreateView.as_view(), name='vehicle-create'),
    
    # EXISTING ENDPOINT: GET /api/vehicles/{vehicle_id}/ - DO NOT MODIFY
    path('<int:vehicle_id>/', views.VehicleDetailView.as_view(), name='vehicle-detail'),
    
    # EXISTING ENDPOINT: PUT /api/vehicles/{vehicle_id}/update/ - DO NOT MODIFY
    path('<int:vehicle_id>/update/', views.VehicleUpdateView.as_view(), name='vehicle-update'),
    
    # EXISTING ENDPOINT: DELETE /api/vehicles/{vehicle_id}/delete/ - DO NOT MODIFY
    path('<int:vehicle_id>/delete/', views.VehicleDeleteView.as_view(), name='vehicle-delete'),
    
    # EXISTING ENDPOINT: POST /api/vehicles/{vehicle_id}/deactivate/ - DO NOT MODIFY
    path('<int:vehicle_id>/deactivate/', views.VehicleDeactivateView.as_view(), name='vehicle-deactivate'),
    
    # EXISTING ENDPOINT: POST /api/vehicles/{vehicle_id}/toggle-online/ - DO NOT MODIFY
    path('<int:vehicle_id>/toggle-online/', views.VehicleToggleOnlineView.as_view(), name='vehicle-toggle-online'),
    
    # EXISTING ENDPOINT: POST /api/vehicles/{vehicle_id}/toggle-offline/ - DO NOT MODIFY
    path('<int:vehicle_id>/toggle-offline/', views.VehicleToggleOfflineView.as_view(), name='vehicle-toggle-offline'),
    
    # EXISTING ENDPOINT: GET /api/vehicles/driver/{driver_id}/ - DO NOT MODIFY
    path('driver/<int:driver_id>/', views.VehiclesByDriverView.as_view(), name='vehicles-by-driver'),

    # Vehicle Config endpoints
    # EXISTING ENDPOINT: GET /api/vehicles/configs/types/ - DO NOT MODIFY
    path('configs/types/', views.VehicleTypeListView.as_view(), name='vehicle-types-list'),
    
    # EXISTING ENDPOINT: GET /api/vehicles/configs/brands/ - DO NOT MODIFY
    path('configs/brands/', views.VehicleBrandListView.as_view(), name='vehicle-brands-list'),
    
    # EXISTING ENDPOINT: GET /api/vehicles/configs/models/ - DO NOT MODIFY
    path('configs/models/', views.VehicleModelListView.as_view(), name='vehicle-models-list'),
    
    # EXISTING ENDPOINT: GET /api/vehicles/configs/colors/ - DO NOT MODIFY
    path('configs/colors/', views.VehicleColorListView.as_view(), name='vehicle-colors-list'),
]