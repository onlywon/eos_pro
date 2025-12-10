from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('event/new/', views.event_create, name='event_create'),
    path('event/<int:event_id>/', views.detail, name='detail'),
    path('event/<int:event_id>/export/', views.export_excel, name='export_excel'),
    
    # ▼▼▼ [삭제 기능 주소] 이게 꼭 있어야 합니다! ▼▼▼
    path('event/<int:event_id>/delete/', views.event_delete, name='event_delete'),
]