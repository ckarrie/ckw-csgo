from django.contrib import admin
from django.utils.html import format_html

from csgomatches import models

@admin.register(models.Organization)
class OrganizationAdmin(admin.ModelAdmin):
	list_display = ("name", "name_long", "slug", "logo_preview")
	search_fields = ("name", "name_long", "slug")
	prepopulated_fields = {"slug": ("name",)}
	readonly_fields = ("logo_preview",)
	fields = ("name", "name_long", "slug", "logo_url", "logo_preview")

	@admin.display(description="Logo")
	def logo_preview(self, obj):
		if obj.logo_url:
			return format_html(
				'<img src="{}" alt="{}" style="max-height: 40px;" />',
				obj.logo_url,
				obj.name,
			)
		return "-"
