from django.contrib import admin

from .models import Group, Post, Comment, Follow


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'author', 'group', 'pub_date')
    list_editable = ('group',)
    search_fields = ('text',)
    empty_value_display = '-пусто-'
    list_filter = ('pub_date',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'post', 'author', 'text', 'created',)
    search_fields = ('text',)
    empty_value_display = '-пусто-'
    list_filter = ('created',)


admin.site.register(Group)
admin.site.register(Follow)
