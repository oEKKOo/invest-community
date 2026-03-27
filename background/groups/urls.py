from django.urls import path

from . import views

urlpatterns = [
    path('groups/my-invites/', views.my_group_invites, name='my_group_invites'),
    path('groups/', views.groups_list_create, name='groups_list_create'),
    path('groups/<int:group_id>/', views.group_detail, name='group_detail'),
    path('groups/<int:group_id>/join/', views.group_join, name='group_join'),
    path('groups/<int:group_id>/leave/', views.group_leave, name='group_leave'),
    path('groups/<int:group_id>/members/', views.group_members, name='group_members'),
    path('groups/<int:group_id>/members/<int:user_id>/role/', views.group_member_set_role, name='group_member_set_role'),
    path('groups/<int:group_id>/transfer-owner/', views.group_transfer_owner, name='group_transfer_owner'),
    path('groups/<int:group_id>/join-requests/', views.group_join_requests, name='group_join_requests'),
    path('groups/<int:group_id>/join-requests/<int:request_id>/review/', views.group_join_request_review, name='group_join_request_review'),
    path('groups/<int:group_id>/reviewers/', views.group_reviewers, name='group_reviewers'),
    path('groups/<int:group_id>/reviewers/<int:user_id>/', views.group_reviewer_delete, name='group_reviewer_delete'),
    path('groups/<int:group_id>/invites/', views.group_invites, name='group_invites'),
    path('groups/<int:group_id>/invites/<int:invite_id>/respond/', views.group_invite_respond, name='group_invite_respond'),
    path('groups/<int:group_id>/posts/', views.group_posts, name='group_posts'),
    path('groups/<int:group_id>/files/', views.group_files, name='group_files'),
    path('groups/<int:group_id>/files/<int:file_id>/', views.group_file_delete, name='group_file_delete'),
]
