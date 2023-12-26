page = {
  "html_base": null,
  "param": {},
}


function getPageContent() {

  // Получение значения якоря из текущего URL
  var anchor = window.location.href.split('?')[0].split('#')[1];

  // Если якорь отсутствует, используем "dashboard" по умолчанию
  if (!anchor || anchor === "") {
    anchor = "profile";
    // Заменяем якорь в текущем URL
    var newUrl = window.location.pathname + "#" + anchor;
    // Обновляем URL без перезагрузки страницы
    window.history.pushState({}, '', newUrl);
  }

  // Показ прелоадера
  showLoader();
  // AJAX запрос для получения HTML-части страницы
  $.ajax({
    url: '/partner/get_page/',
    method: 'GET',
    dataType: 'json',
    data: { p: anchor },
    success: function (response) {
      // Сохранение полученного HTML в локальное хранилище
      page["html"] = response.html;
      page["breadcrumbs"] = response.content.breadcrumbs;
      page["title"] = response.content.title;
      page["param"] = response.param;
      page["page_id"] = response.page_id;

      document.title = "Кабинет партнера - " + page["title"]
      history.pushState({ "page": anchor }, page["title"], window.location.href);

      updateHeaderAndMenu();

      // Инициализация страницы
      initializePage();

      // Скрытие прелоадера и отображение содержимого страницы
      hideLoader();
      showPage();
    },
    error: function () {
      console.log('Ошибка при получении данных');
    }
  });
}

function restoreSettings() {
  // Код для восстановления настроек из локального хранилища
  // (например, чтение значений и применение их к элементам на странице)
}

function initializePage() {
  // Код для инициализации страницы (например, инициализация таблицы статистики)
  $('.main-content .base-content').html(page["html"])


  if (page["page_id"] == "stat") {
    param = {
      "type": "kdjq.option",
      "kdjq_id": "stat.promocode",
    }

    $.ajax({
      url: '/partner/api/get/',
      method: 'GET',
      dataType: 'json',
      data: param,
      success: function (response) {
        kdjq_option = response.kdjq_option
        $('.kdjq_stat').kdjq(kdjq_option);
      },
      error: function () { console.log('Ошибка при получении данных'); }
    });
  }
}

function showPage() {
  // Отображение содержимого страницы
  $('.base-content').show()
}

function showLoader() {
  // Показ прелоадера (например, добавление элемента с прелоадером в DOM)
  $('.main-content > *').hide()
  $(".page-loader").css({ opacity: 0 })
  $(".page-loader").show()
  $(".page-loader").animate({}, 1000, function () { $(".page-loader").animate({ opacity: 1 }, 500, function () { }); });
}

function hideLoader() {
  // Скрытие прелоадера (например, удаление элемента с прелоадером из DOM)
  $(".page-loader").hide()
  $('.main-content > *').not(".page-loader").show()
}

function updateHeaderAndMenu() {
  // Обновление хлебных крошек
  var breadcrumbs = page.breadcrumbs;
  var breadcrumbsElement = $('.breadcrumbs .items');
  breadcrumbsElement.empty();

  // Добавление остальных элементов
  if (breadcrumbs) {
    for (var i = 0; i < breadcrumbs.length; i++) {
      var breadcrumbItem = $('<div>').addClass('item').text(breadcrumbs[i]);
      breadcrumbsElement.append(breadcrumbItem);
    }
  }

  // Обновление заголовка
  var titleElement = $('.breadcrumbs .title');
  titleElement.text(page.title);
}

function sand_ajax_form(form_id) {

  param = {
    "form_id": form_id,
  }

  $("div.kdjq-form[form-id='" + form_id + "'] :input").each(function () {
    var fieldName = $(this).attr("name");
    var fieldValue = $(this).val();
    if (fieldName != undefined)
      param[fieldName] = fieldValue;
  });



  $.ajax({
    url: '/partner/api/form/',
    method: 'POST',
    dataType: 'json',
    data: param,
    beforeSend: function (request) {
      request.setRequestHeader('X-CSRFToken', getCookie('csrftoken'))
    },
    success: function (response) {
      getPageContent()
    },
    error: function () {
      console.log('Ошибка при получении данных');
    }
  });
}

$(document).ready(function () {
  $(window).on("hashchange", function () {
    getPageContent()
  });

  $(`body`).on("click", `.kdjq-card--header--buttons--item[button-event="hide"]`, function () {
    $(this).parents('.kdjq-card').toggleClass('hide')
  })

  $(`body`).on("click", `.list .button-menu`, function () {
    $(this).toggleClass('active')
    $(this).parent().find('.item-menu').toggleClass('show')
  })

  $(`body`).on("click", `.kdjq-form button[type="submit"]`, function () {
    sand_ajax_form($(this).parents('.kdjq-form').attr("form-id"))
  })

  $(`body`).on("click", `.promocodes-item .item-menu-item[button-event="edit"]`, function () {
    let id = $(this).parents(".promocodes-item").attr("promocode-id")
    $("#promocode_edit_pane #input_item_id").val(id)
    $("#promocode_edit-tab").click()
    promocode_edit_form_restart()
  })


  $(`body`).on("click", `.promocodes-item .item-menu-item[button-event="remove"]`, function () {
    let id = $(this).parents(".promocodes-item").attr("promocode-id")
    if (page["page_id"] == "promocode") {
      param = {
        "form_id": "promocode.remove",
        "promocode_id": id,
      }

      $.ajax({
        url: '/partner/api/form/',
        method: 'POST',
        dataType: 'json',
        data: param,
        beforeSend: function (request) { request.setRequestHeader('X-CSRFToken', getCookie('csrftoken')) },
        success: function (response) { getPageContent() },
        error: function () { console.log('Ошибка при получении данных'); }
      });
    }
  })

  $(`body`).on("click", `.promocodes-item .item-menu-item[button-event="turn_off"], .promocodes-item .item-menu-item[button-event="turn_on"]`, function () {
    let id = $(this).parents(".promocodes-item").attr("promocode-id")

    if (page["page_id"] == "promocode") {
      param = {
        "form_id": "promocode.switch_enable",
        "promocode_id": id,
      }

      $.ajax({
        url: '/partner/api/form/',
        method: 'POST',
        dataType: 'json',
        data: param,
        beforeSend: function (request) { request.setRequestHeader('X-CSRFToken', getCookie('csrftoken')) },
        success: function (response) { getPageContent() },
        error: function () { console.log('Ошибка при получении данных'); }
      });
    }
  })

  $(`body`).on("change", `#promocode_edit_pane #input_item_id`, function () {
    promocode_edit_form_restart()
  });

  function promocode_edit_form_restart() {
    $form = $("#promocode_edit_pane")

    let id = $(`#promocode_edit_pane #input_item_id`).val()
    if (page["page_id"] == "promocode") {
      let obj = page["param"]["promocodes"][id]
      $form.find(`#input_name`).val(obj["name"])
      $form.find(`#input_description`).val(obj["description"])
      $form.find(`#input_code`).val(obj["code"])
      $form.find(`#input_cashback`).val(obj["cashback"])
      $form.find(`#input_hotel_type`).val(obj["hotel_type"])
      $form.find(`#input_date_before_day`).val(obj["date_before_day"])
      $form.find(`#duration_indefinite`).val(obj["on_indefinite"])
      $form.find(`#input_channel_id`).val(obj["channel"])
    }

    if (page["page_id"] == "channel") {
      let obj = page["param"]["channels"][id]
      $form.find(`#input_name`).val(obj["name"])
      $form.find(`#input_url`).val(obj["url"])
    }

  }



  // Восстановление настроек, если они есть в локальном хранилище
  restoreSettings();


  // Вызов функции для получения содержимого страницы
  getPageContent();
});
