// Функция для форматирования даты
function formatDate(date) {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const seconds = Math.floor(diff / 1000);

  if (seconds < 10) {
    return "Сейчас";
  } else if (seconds < 60) {
    return `${seconds} секунд назад`;
  }

  const minutes = Math.floor(diff / 1000 / 60);
  if (minutes === 1) {
    return `Минуту назад`;
  } else if (minutes < 60) {
    return `${minutes} минут назад`;
  }

  const hours = Math.floor(diff / 1000 / 60 / 60);
  if (hours === 1) {
    return `Час назад`;
  } else if (hours < 12) {
    return `${hours} часов назад`;
  }

  return date.toLocaleDateString('ru-RU', { year: 'numeric', month: 'long', day: 'numeric', hour: 'numeric', minute: 'numeric' });
}


// Функция для получения уведомлений и обновления контейнера
function updateNotificationsContainer() {
  const notificationsContainer = $('#notificationsContainer');
  const notificationsContainer_list = $('#notificationsContainer .list');

  // Очищаем контейнер
  notificationsContainer_list.empty();

  // AJAX запрос для получения уведомлений
  $.ajax({
    url: '/api/notice/get/',
    type: 'GET',
    dataType: 'json',
    success: function (request) {
      // Перебираем уведомления и добавляем их в контейнер
      request.notices.forEach(function (notification) {
        const createdAt = new Date(notification.created_at);
        const formattedCreatedAt = formatDate(createdAt);
        const html = `
          <div class="notification">
            <p class="title">${notification.title}</p>
            <p class="text">${notification.text}</p>
            <p class="createdAt">${formattedCreatedAt}</p>
          </div>
        `;
        notificationsContainer_list.append(html);
      });
    }
  });
}

$(document).ready(function () {
  // Обработчик клика по кнопке "Показать уведомления"
  $('#showNotificationsBtn').on('click', function () {
    const notificationsContainer = $('#notificationsContainer');
    if (notificationsContainer.hasClass('hide')) {
      // Показываем контейнер
      updateNotificationsContainer();
      notificationsContainer.removeClass("hide");
    }
  });

  $('#notificationsContainerClose').on('click', function () {
    $("#notificationsContainer").addClass("hide")
  })

  updateNotificationsContainer()
});

// Обновляем уведомления каждые 10 секунд
// setInterval(updateNotificationsContainer, 10000);