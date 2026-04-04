from django.contrib import admin
from .models import Review, ReviewMedia
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["product_id","user_id","rating","is_approved","created_at"]
    list_filter = ["is_approved","rating"]
admin.site.register(ReviewMedia)
