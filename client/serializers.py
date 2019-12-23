from rest_framework import serializers

class SublistSerializer(serializers.Serializer):
    sublist_id = serializers.RegexField('[a-zA-z0-9]{22}')