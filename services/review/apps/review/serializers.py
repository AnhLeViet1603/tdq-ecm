from rest_framework import serializers
from .models import Review, ReviewMedia

class ReviewMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewMedia
        exclude = ["review"]

class ReviewSerializer(serializers.ModelSerializer):
    media = ReviewMediaSerializer(many=True, read_only=True)
    class Meta:
        model = Review
        fields = "__all__"
        read_only_fields = ["user_id","is_approved","helpful_count"]
