from rest_framework import serializers

from .models import Group, GroupMember, GroupJoinRequest, GroupReviewer, GroupInvite, GroupPost, GroupFile


class GroupMemberSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source='user_id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    displayName = serializers.CharField(source='user.display_name', read_only=True)
    avatar = serializers.CharField(source='user.avatar_url', read_only=True)
    joinedAt = serializers.DateTimeField(source='joined_at', read_only=True)

    class Meta:
        model = GroupMember
        fields = ['id', 'userId', 'username', 'displayName', 'avatar', 'role', 'status', 'joinedAt']


class GroupSerializer(serializers.ModelSerializer):
    ownerId = serializers.IntegerField(source='owner_id', read_only=True)
    ownerName = serializers.CharField(source='owner.display_name', read_only=True)
    tags = serializers.JSONField(source='tags_json', read_only=True)
    topicDirection = serializers.CharField(source='topic_direction', read_only=True)
    avatar = serializers.CharField(source='avatar_url', read_only=True)
    memberCount = serializers.IntegerField(source='member_count', read_only=True)
    postCount = serializers.IntegerField(source='post_count', read_only=True)
    fileCount = serializers.IntegerField(source='file_count', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Group
        fields = [
            'id', 'name', 'slug', 'description', 'avatar', 'tags', 'topicDirection',
            'visibility', 'status', 'ownerId', 'ownerName',
            'memberCount', 'postCount', 'fileCount', 'createdAt',
        ]


class GroupCreateUpdateSerializer(serializers.ModelSerializer):
    tags = serializers.JSONField(source='tags_json', required=False)
    topicDirection = serializers.CharField(source='topic_direction', required=False, allow_blank=True)
    avatar = serializers.URLField(source='avatar_url', required=False, allow_blank=True)

    class Meta:
        model = Group
        fields = ['name', 'description', 'avatar', 'tags', 'topicDirection', 'visibility']


class GroupJoinRequestSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source='user_id', read_only=True)
    userName = serializers.CharField(source='user.display_name', read_only=True)
    reviewedBy = serializers.IntegerField(source='reviewed_by_id', read_only=True)
    reviewNote = serializers.CharField(source='review_note', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    reviewedAt = serializers.DateTimeField(source='reviewed_at', read_only=True)

    class Meta:
        model = GroupJoinRequest
        fields = [
            'id', 'group_id', 'userId', 'userName', 'status', 'message',
            'reviewedBy', 'reviewNote', 'createdAt', 'reviewedAt',
        ]


class GroupPostSerializer(serializers.ModelSerializer):
    groupId = serializers.IntegerField(source='group_id', read_only=True)
    authorId = serializers.IntegerField(source='author_id', read_only=True)
    authorName = serializers.CharField(source='author.display_name', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = GroupPost
        fields = [
            'id', 'groupId', 'authorId', 'authorName',
            'title', 'body', 'content_type', 'status',
            'like_count', 'comment_count', 'createdAt',
        ]


class GroupPostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupPost
        fields = ['title', 'body', 'content_type']


class GroupReviewerSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source='user_id', read_only=True)
    userName = serializers.CharField(source='user.display_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = GroupReviewer
        fields = ['id', 'group_id', 'userId', 'userName', 'username', 'createdAt']


class GroupInviteSerializer(serializers.ModelSerializer):
    groupId = serializers.IntegerField(source='group_id', read_only=True)
    groupName = serializers.CharField(source='group.name', read_only=True)
    groupVisibility = serializers.CharField(source='group.visibility', read_only=True)
    inviterId = serializers.IntegerField(source='inviter_id', read_only=True)
    inviterName = serializers.CharField(source='inviter.display_name', read_only=True)
    inviteeId = serializers.IntegerField(source='invitee_id', read_only=True)
    inviteeName = serializers.CharField(source='invitee.display_name', read_only=True)
    respondedAt = serializers.DateTimeField(source='responded_at', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = GroupInvite
        fields = [
            'id', 'groupId', 'groupName', 'groupVisibility', 'inviterId', 'inviterName', 'inviteeId', 'inviteeName',
            'status', 'message', 'respondedAt', 'createdAt',
        ]


class GroupFileSerializer(serializers.ModelSerializer):
    groupId = serializers.IntegerField(source='group_id', read_only=True)
    uploadedBy = serializers.IntegerField(source='uploaded_by_id', read_only=True)
    uploadedByName = serializers.CharField(source='uploaded_by.display_name', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    fileUrl = serializers.SerializerMethodField()

    class Meta:
        model = GroupFile
        fields = [
            'id', 'groupId', 'uploadedBy', 'uploadedByName',
            'original_name', 'mime_type', 'file_size',
            'visibility', 'status', 'createdAt', 'fileUrl',
        ]

    def get_fileUrl(self, obj):
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url if obj.file else ''
