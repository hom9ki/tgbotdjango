from django.contrib import admin
from .models import UploadedFile, Nomenclature, Warehouse, MinStock, Completeness


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ('title', 'doc_type')
    list_filter = ('uploaded_by', 'title', 'doc_type')
    readonly_fields = ('uploaded_by', 'created_at')

    class Meta:
        model = UploadedFile


@admin.register(Nomenclature)
class NomenclatureAdmin(admin.ModelAdmin):
    list_display = ('manufacturer', 'catalog_number')
    search_fields = ('manufacturer', 'catalog_number', 'name')
    search_help_text = 'Поиск по брендам, номеру по каталогу и наименованию...'
    show_full_result_count = True
    list_filter = ('manufacturer',)
    date_hierarchy = 'updated_at'
    list_per_page = 50
    fields = ('manufacturer', 'catalog_number', 'name')


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'code', 'active')
    fields = ('name', 'short_name', 'code', 'active')
    search_fields = ('name', 'code', 'short_name')
    list_filter = ('active',)


@admin.register(MinStock)
class MinStockAdmin(admin.ModelAdmin):
    list_display = ('nomenclature__manufacturer', 'nomenclature__catalog_number', 'warehouse', 'active', 'min_quantity',
                    'last_updated')
    fields = ('nomenclature', 'warehouse', 'active', 'min_quantity')
    search_fields = ('nomenclature__manufacturer', 'nomenclature__catalog_number')
    list_filter = ('warehouse', 'active')
    date_hierarchy = 'last_updated'
    list_per_page = 50


@admin.register(Completeness)
class CompletenessAdmin(admin.ModelAdmin):
    list_display = ('count', 'active', 'nomenclatures_count')
    fields = ('nomenclatures', 'count', 'active')
    list_filter = ('count', 'active')
    search_fields = ('nomenclatures__manufacturer', 'nomenclatures__catalog_number')

    def nomenclatures_count(self, obj):
        return obj.nomenclatures.count()

    nomenclatures_count.short_description = 'Количество позиций'
