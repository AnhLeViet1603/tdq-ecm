from django.contrib import admin
from .models import (
    KnowledgeDocument, FAQCategory, FAQ, ProductKnowledge, VectorIndex
)


@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ['doc_id', 'doc_type', 'title', 'language', 'is_active', 'created_at']
    list_filter = ['doc_type', 'language', 'is_active', 'created_at']
    search_fields = ['doc_id', 'title', 'content']
    readonly_fields = ['created_at', 'updated_at', 'vector_id']
    fieldsets = (
        ('Basic Information', {
            'fields': ('doc_id', 'doc_type', 'title', 'language', 'is_active')
        }),
        ('Content', {
            'fields': ('content', 'summary')
        }),
        ('Metadata', {
            'fields': ('metadata', 'source', 'vector_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(FAQCategory)
class FAQCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'sort_order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'priority', 'is_active', 'views_count', 'helpful_count']
    list_filter = ['category', 'is_active', 'priority', 'created_at']
    search_fields = ['question', 'answer']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'question', 'answer', 'priority', 'is_active')
        }),
        ('Metadata', {
            'fields': ('keywords', 'related_products')
        }),
        ('Analytics', {
            'fields': ('views_count', 'helpful_count', 'not_helpful_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ProductKnowledge)
class ProductKnowledgeAdmin(admin.ModelAdmin):
    list_display = ['product_id', 'product_name', 'created_at']
    list_filter = ['created_at']
    search_fields = ['product_id', 'product_name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('product_id', 'product_name')
        }),
        ('Knowledge Content', {
            'fields': ('expert_tips', 'common_issues', 'usage_guide')
        }),
        ('Technical Details', {
            'fields': ('specifications', 'compatibility_info', 'maintenance_tips'),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': ('video_tutorials', 'related_docs'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(VectorIndex)
class VectorIndexAdmin(admin.ModelAdmin):
    list_display = ['index_name', 'index_type', 'dimension', 'document_count', 'is_active', 'last_updated']
    list_filter = ['index_type', 'is_active', 'last_updated']
    search_fields = ['index_name']
    readonly_fields = ['created_at', 'updated_at', 'last_updated']
