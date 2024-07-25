from django.urls import path

from authorization.views import RoleListView, RoleCreateView, RoleEditView, RoleDeleteView, \
    UsersListView, UserCreateView, UserEditView, UserDeleteView, \
    LoginView, CustomLogoutView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    # User
    path("user/list", UsersListView.as_view(), name="user_list"),
    path('user/create', UserCreateView.as_view(), name='create_user'),
    path("user/edit/<int:pk>/", UserEditView.as_view(), name="user_edit"),
    path("user/delete/<int:pk>/", UserDeleteView.as_view(), name="user_delete"),
    # Role
    path("roles/list/", RoleListView.as_view(), name='role_list'),
    path('roles/create/', RoleCreateView.as_view(), name='create_role'),
    path('roles/edit/<int:role_id>/', RoleEditView.as_view(), name='edit_role'),
    path('roles/delete/<int:pk>/', RoleDeleteView.as_view(), name='role_delete'),
]
