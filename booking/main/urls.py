from django.urls import path, include
from main.views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'api/realty', RealtyViewSet, basename='realty')


urlpatterns = [
    path('api/user/<str:login>/', userDetail, name='userDetail'),
    path('api/auth/', login, name='login'), 
    path('api/auth/register', register, name='auth_register'), #POST
    path('api/realty/search', RealtySearchViewSet, name='realty_search'),

    path('', include(router.urls)),
    path("Storage/Item/<str:itemId>", item, name="storageItem"),
    path("api/feedback/", FeedbackView.as_view(), name="feedback"),

    path('api/booking-item', BookingView.as_view(), name='booking_item'),
    path('api/booking-item/<uuid:id>/', BookingDetailView.as_view(), name='booking_item'),
]


#
    #path('api/user/<str:login>/add-card/', add_card_view, name='add_card'), #POST
    #path('api/user/', user_create_view, name='user_create'), #POST
    #path('api/user/', user_update_view, name='user_update'), #PATCH
    #path('api/user/', user_delete_view, name='user_delete'), #DELETE
    #path('Administrator/GetUsersTable/', admin_users_table_view, name='admin_users_table'), #GET

    #path('api/realty/all/', all_realty_view, name='all_realty'), #GET
    #path('api/realty/<uuid:id>/', realty_detail_view, name='realty_detail'), #GET
    #path('api/realty/search/', realty_search_view, name='realty_search'), #GET
    #path('api/realty/', realty_create_view, name='realty_create'), #POST
    #path('api/realty/', realty_update_view, name='realty_update'), #PATCH
    #path('api/realty/<slug:slug>/', realty_delete_view, name='realty_delete'), #DELETE
    #path('Administrator/GetRealtiesTable/', admin_realties_table_view, name='admin_realties_table'), #GET

    #path('api/booking-item/<uuid:id>/', booking_item_view, name='booking_item'), #POST
    
    #path('api/feedback/<uuid:id>/', delete_feedback_view, name='delete_feedback'), #DELETE
    #path('resources/images/<str:imageUrl>', loadImage, name='loadImage')