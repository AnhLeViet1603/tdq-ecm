from django.contrib import admin
from .models import UserBehavior, RecommendationModel, ProductEmbedding, RecommendationCache


@admin.register(UserBehavior)
class UserBehaviorAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'action_type', 'product_id', 'timestamp', 'created_at']
    list_filter = ['action_type', 'timestamp', 'created_at']
    search_fields = ['user_id', 'product_id', 'search_query']
    readonly_fields = ['created_at', 'updated_at', 'timestamp']
    date_hierarchy = 'timestamp'


@admin.register(RecommendationModel)
class RecommendationModelAdmin(admin.ModelAdmin):
    list_display = ['model_name', 'model_type', 'version', 'is_active', 'accuracy', 'last_trained_at']
    list_filter = ['model_type', 'is_active', 'last_trained_at']
    search_fields = ['model_name', 'model_type']
    readonly_fields = ['created_at', 'updated_at', 'last_trained_at']
    actions = ['activate_models']

    def activate_models(self, request, queryset):
        """Activate selected models and deactivate others of the same type"""
        count = 0
        for model in queryset:
            # Deactivate other models of the same type
            RecommendationModel.objects.filter(
                model_type=model.model_type,
                is_active=True
            ).exclude(id=model.id).update(is_active=False)

            # Activate this model
            model.is_active = True
            model.save()
            count += 1

        self.message_user(request, f'{count} model(s) activated successfully.')

    activate_models.short_description = "Activate selected models"


@admin.register(ProductEmbedding)
class ProductEmbeddingAdmin(admin.ModelAdmin):
    list_display = ['product_id', 'embedding_model', 'vector_dimension', 'created_at']
    list_filter = ['embedding_model', 'created_at']
    search_fields = ['product_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(RecommendationCache)
class RecommendationCacheAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'algorithm_used', 'generated_at', 'expires_at', 'hit_count']
    list_filter = ['algorithm_used', 'generated_at', 'expires_at']
    search_fields = ['user_id']
    readonly_fields = ['created_at', 'updated_at', 'generated_at']
    date_hierarchy = 'generated_at'
