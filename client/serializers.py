from rest_framework import serializers

class PlaylistSerializer(serializers.Serializer):
    playlist_id = serializers.RegexField('[a-zA-z0-9]{22}')
    has_local_changes = serializers.BooleanField(default=False)

class SublistSerializer(serializers.Serializer):
    sublist_id = serializers.RegexField('[a-zA-z0-9]{22}')
