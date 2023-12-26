from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import *

class ChatAdmin(admin.ModelAdmin):
    list_display = ("id", "display_users", "count_messages", "created_at", "display_data")
    search_fields = ['users__username', "users__email", "users__id"]
    list_per_page = 2000



    def count_messages(self, obj : Chat):
      return obj.messages.count()

    count_messages.short_description = 'Количество сообщений'

    def display_data(self, obj):
      # Проверяем, что поле data содержит JSON
      if isinstance(obj.data, dict):
          # Преобразуем ключи и значения JSON в HTML теги
          html_tags = "<div class='html_tegs' style='display: flex; flex-direction: row; gap: 4px;'>"

          order = [
            "type",
            "hotel", "title",
            "booking", "text",
          ]

          items = obj.data.items()

          items = sorted(items, key=lambda x: order.index(x[0]))

          for key, value in items:
              color = "#9E9E9E"

              if key == "type":
                color = "#ff8989"

              if key in ["hotel", "title"]:
                color = "#d679d1"

              if key in ["booking", "text"]:
                color = "#217dff"


              html_tags += f"""
                <div class="tag" style="background: {color}; padding: 4px; width: max-content; border-radius: 5px; color: white;">
                  <span class="key" style="font-weight: 900;">{key} > </span>
                  <span class="value">{value}</span>
                </div>
              """

          # Возвращаем HTML код в виде строки
          html_tags += "</div>"
          return mark_safe(html_tags)
      else:
          return ''

    display_data.short_description = 'Data'

    def display_users(self, obj):
      # Проверяем, что поле data содержит JSON

        # Преобразуем ключи и значения JSON в HTML теги
        html_tags = "<div class='html_tegs' style='display: flex; flex-direction: row; gap: 4px;'>"

        for user in obj.users.all():

            value = str(user)

            color = "#ff8989"

            if user.user_type in ["admin", "moder", "owner"]:
              color = "#d679d1"

            if user.user_type in ["hotel"]:
              color = "#217dff"


            html_tags += f"""
              <div class="tag" style="background: {color}; padding: 4px; width: max-content; border-radius: 5px; color: white;">
                <span class="value">{value}</span>
              </div>
            """

        html_tags += "</div>"

        return mark_safe(html_tags)

    display_users.short_description = 'Пользователи'


admin.site.register(Chat, ChatAdmin)


class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "text", "datetime", "param")
    search_fields = ['user__username', "user__email", "user__id", "text"]
    list_per_page = 500

admin.site.register(Message, MessageAdmin)