$(".search-buttons .item").not("#hotel_place_select").click(function () {
  category = $(this).parent(".search-buttons").data("type")
  type = $(this).data("type")

  $(`.search-buttons[data-type="${category}"] .item`).removeClass("select")
  $(`.search-buttons[data-type="${category}"] .item[data-type="${type}"]`).addClass("select")

  filter_apply()
})

$(".search-buttons .item#hotel_place_select").click(function () {
  category = $(this).parent(".search-buttons").data("type")
  type = $(this).data("type")

  $(`.search-buttons[data-type="${category}"] .item`).removeClass("select")
  $(`.search-buttons[data-type="${category}"] .item#hotel_place_select`).addClass("select")

  filter_apply()
})

$("#search-input").change(function (e) {
  filter_apply()
});


function filter_apply() {

  let list_filter_param = {}

  $(".search-buttons .item.select").each(function () {
    let category = $(this).parent(".search-buttons").data("type")
    if (category == "hotel_place" && $("#hotel_place_select").hasClass("select")) {
      list_filter_param[category] = hotel_place_select_id
    }
    else {
      let val = $(this).data("type");
      list_filter_param[category] = val
    }
  });
  list_filter_param["search"] = $("#search-input").val()


  console.log("Фильтер собран")
  console.table(list_filter_param)

  // Фильтрация
  let keys = Object.keys(moder_works).reverse()

  let hide_tr = []

  keys.forEach((key, index) => {

    let obj = moder_works[key]

    let valid_count = 0

    let valid = true

    if (list_filter_param["hotel_status"] == "active") {
      obj["hotels"].forEach((hotel) => {
        if (hotel.status.code == "active") {
          valid_count += 1
        }
      })
    }

    if (list_filter_param["hotel_status"] == "on_moderation") {
      obj["hotels"].forEach((hotel) => {
        if (hotel.status.code == "is_pending") {
          valid_count += 1
        }
      })
    }

    if (list_filter_param["hotel_status"] == "off") {
      obj["hotels"].forEach((hotel) => {
        if (!hotel.enable) {
          valid_count += 1
        }
      })
    }

    if (list_filter_param["hotel_status"] == "on") {
      obj["hotels"].forEach((hotel) => {
        if (hotel.enable) {
          valid_count += 1
        }
      })
    }

    if (list_filter_param["hotel_status"] != "all") {
      if (valid_count == 0) {
        valid = false
      }
    }

    valid_count = 0

    if (list_filter_param["hotel_type"] != "all") {
      obj["hotels"].forEach((hotel) => {
        let hotel_type = list_filter_param["hotel_type"]
        if (hotel.type == hotel_type) {
          valid_count += 1
        }
      })
    }


    let all_hotel_name_str = ""
    let all_hotel_city_str = ""
    obj["hotels"].forEach((hotel) => {
      all_hotel_name_str += hotel.name + " "
      all_hotel_city_str += hotel.city + " "
    })

    all_hotel_name_str = all_hotel_name_str.trim().toLowerCase()
    all_hotel_city_str = all_hotel_city_str.trim().toLowerCase()



    if (list_filter_param["hotel_type"] != "all") {
      if (valid_count == 0) {
        valid = false
      }
    }

    if (valid == true) {
      $(`tr[data-id='${key}']`).show()
    }
    else {
      $(`tr[data-id='${key}']`).hide()
    }

    valid_count = 0


    if (list_filter_param["work_status"] != "all") {
      if (list_filter_param["work_status"] == obj["param"]["status"]) {
        valid_count = 1
      }
    }

    if (list_filter_param["work_status"] != "all") {
      if (valid_count == 0) {
        valid = false
      }
    }

    if (valid == true) {
      $(`tr[data-id='${key}']`).show()
    }
    else {
      $(`tr[data-id='${key}']`).hide()
    }

    if (list_filter_param["work_status"] != "all") {
      if (list_filter_param["work_status"] == obj["param"]["status"]) {
        valid_count = 1
      }
    }

    if (list_filter_param["work_status"] != "all") {
      if (valid_count == 0) {
        valid = false
      }
    }

    if (valid == true) {
      $(`tr[data-id='${key}']`).show()
    }
    else {
      $(`tr[data-id='${key}']`).hide()
    }





    if (list_filter_param["last_status_work"] != "all") {
      last_index = obj["status"].length - 1
      if (last_index >= 0 && list_filter_param["last_status_work"] == obj["status"][last_index]["value"]) {
        valid_count = 1
      }
    }

    if (list_filter_param["last_status_work"] != "all") {
      if (valid_count == 0) {
        valid = false
      }
    }

    if (valid == true) {
      $(`tr[data-id='${key}']`).show()
    }
    else {
      $(`tr[data-id='${key}']`).hide()
    }




    valid_count = 0

    if (list_filter_param["user_status"] != "all") {
      if (obj["user"]["email"]["status"]) {
        valid_count = 1
      }
      if (obj["user"]["phone"]["status"]) {
        valid_count = 1
      }
    }

    if (list_filter_param["user_status"] != "all") {
      if (valid_count == 0) {
        valid = false
      }
    }

    if (valid == true) {
      $(`tr[data-id='${key}']`).show()
    }
    else {
      $(`tr[data-id='${key}']`).hide()
    }

    valid_count = 0


    if (list_filter_param["user_staff_id"] != "all") {
      if (obj["moder"] == list_filter_param["user_staff_id"]) {
        valid_count = 1
      }
    }

    if (list_filter_param["user_staff_id"] != "all") {
      if (valid_count == 0) {
        valid = false
      }
    }

    if (valid == true) {
      $(`tr[data-id='${key}']`).show()
    }
    else {
      $(`tr[data-id='${key}']`).hide()
    }

    valid_count = 0

    if (list_filter_param["hotel_place"] != "all") {
      obj["hotels"].forEach((hotel) => {
        if (list_filter_param["hotel_place"].indexOf(hotel.city) !== -1) {
          valid_count += 1
        }
      });
    }

    if (list_filter_param["hotel_place"] != "all") {
      if (valid_count == 0) {
        valid = false
      }
    }

    if (valid == true) {
      $(`tr[data-id='${key}']`).show()
    }
    else {
      $(`tr[data-id='${key}']`).hide()
    }


    valid_count = 0

    if (list_filter_param["search"] != "") {
      let search = list_filter_param["search"].toLowerCase()

      if (all_hotel_name_str.length != 0)
        valid_count += all_hotel_name_str.indexOf(search.toLowerCase()) > -1 ? 1 : 0

      if (all_hotel_city_str.length != 0)
        valid_count += all_hotel_city_str.indexOf(search.toLowerCase()) > -1 ? 1 : 0

      valid_count += obj["user"]["fio"]["full"].indexOf(search) > -1 ? 1 : 0
      valid_count += obj["user"]["phone"]["value"].indexOf(search) > -1 ? 1 : 0
      valid_count += obj["user"]["email"]["value"].indexOf(search) > -1 ? 1 : 0
    }

    if (list_filter_param["search"] != "") {
      if (valid_count == 0) {
        valid = false
      }
    }

    if (valid == true) {
      $(`tr[data-id='${key}']`).show()
    }
    else {
      $(`tr[data-id='${key}']`).hide()
    }
  })
}



moder_works = {}


function get_moder_works(id = null) {
  data = {}
  if (id) {
    data["id"] = id
  }

  $.ajax({
    url: "/admin/moderwork/api/get/list/",
    type: "GET",
    data: data,
    success: function (response) {
      for (key in response.moder_works) {
        let id = response.moder_works[key]["id"]
        moder_works[id] = response.moder_works[key]

        removeAllReminder();

        moder_works[id]["reminders"].forEach((item) => {
          if (item.status == "active") {
            addReminder(item.value, item.datetime * 1000);
          }
        });

      }
      reset_record_all()
    }
  });
}

get_moder_works()

function updateElementsFormatTimestamp() {
  $('[data-format-time]').each(function () {
    const timestamp = parseInt($(this).data('time'));
    const date = new Date(timestamp * 1000);
    const formattedDate = date.toLocaleString();
    $(this).text(formattedDate);
  });
}

updateElementsFormatTimestamp();

$('body').on("click", `[data-type-col="hotels"] .item`, function () {

  let id = parseInt($(this).parents("tr").data("id"))
  let obj = moder_works[id]

  id_hotel = $(this).data("id")

  let hotel = null
  obj["hotels"].forEach((item) => {
    if (item["id"] == id_hotel) {
      hotel = item
      return
    }
  })


  id_user = obj["user"]["id"]
  hotel_enable = hotel["enable"]

  let enableOnButtonStyle = ["50%"];
  if (hotel_enable) {
    enableOnButtonStyle.push("disabled");
  }

  let enableOffButtonStyle = ["50%"];
  if (!hotel_enable) {
    enableOffButtonStyle.push("disabled");
  }

  popup_text = hotel["name"] + "<br>"
  popup_text += hotel["address"]["short"] + "<br>"
  popup_text += hotel["address"]["coordinates"] + "<br>"

  if (obj["user"]["phone"]["value"])
    popup_text += "Телефон: " + obj["user"]["phone"]["value"] + "<br>"


  if (obj["user"]["login"])
    popup_text += "Логин: " + obj["user"]["login"] + "<br>"
  if (obj["user"]["password"])
    popup_text += "Пароль: " + obj["user"]["password"] + "<br>"


  popup_create("Действие", popup_text,
    [
      {
        name: "Войти из под пользователя", fun: user_fun_action, param: ["login", id_user], type: "action", color: "purple", style: "full",
      },
      {
        name: "Открыть чат", type: "action", color: "green", fun: user_fun_action, param: ["open_chat", id_user], style: "full",
      },
      {
        name: "Детальная отеля", param: [`/hotel/${id_hotel}/`, 1], type: "link", color: "gray", style: "full",
      },
      {
        name: "Включить", type: "action", color: "green", fun: hotel_fun_action, param: ["enable_on", id_hotel], style: enableOnButtonStyle,
      },
      {
        name: "Выключить", type: "action", color: "red", fun: hotel_fun_action, param: ["enable_off", id_hotel], style: enableOffButtonStyle,
      },
      {
        name: "Разрешить", type: "action", color: "green", fun: hotel_fun_action, param: ["allow_hotel", id_hotel], style: ["50%", "green"],
      },
      {
        name: "Запретить", type: "action", color: "red", fun: hotel_fun_action, param: ["disallow_hotel", id_hotel], style: ["50%", "red"],
      },
      {
        name: "Закрыть", type: "close", color: "gray", style: "full",
      },
    ]
  )
})

function hotel_fun_action(type, id) {
  if (type == "detal_hotel") {
    location.href = `/hotel/${id}/`
  }
  if (type == "enable_on" || type == "enable_off") {
    let type_enable = type

    $.ajax({
      method: "POST",
      data: { "hotel_id": id, "type_enable": type_enable },
      url: "/admin/ajax/moderator_office/get/",
      beforeSend: function (request) {
        request.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
      },
      success: function (request) {
        location.reload()
      }
    });
  }
  if (type == "disallow_hotel") {
    hotel_name = $(`[hotel-id=${id}]`).data("hotel_name")
    popup_create(
      'Запретить',
      hotel_name,
      [
        {
          name: 'Закрыть',
          type: 'close'
        },
        {
          name: 'Запретить',
          fun: disallow_hotel,
          type: 'use-inputs'
        }
      ],
      [
        [
          { type: 'hidden', name: 'hotel_id', val: id },
          { type: 'textarea', label: 'Комментарий (Причина отмены которую увидит пользователь)', name: 'comment' }
        ]
      ]
    )
  }
  if (type == "allow_hotel") {
    hotel_name = $(`[hotel-id=${id}]`).data("hotel_name")
    popup_create(
      'Разрешить',
      `Вы должны проверить все поля отеля, адрес и кординаты <br>${hotel_name}`,
      [
        {
          name: 'Закрыть',
          type: 'close'
        },
        {
          name: 'Разрешить',
          fun: allow_hotel,
          type: 'use-inputs'
        }
      ],
      [
        [
          { type: 'hidden', name: 'hotel_id', val: id },
          { type: 'textarea', label: 'Комментарий (Причина отмены которую увидит пользователь)', name: 'comment' }
        ]
      ],
      "warning"
    )
  }
}

function disallow_hotel(param) {
  $.ajax({
    method: 'POST',
    data: param,
    url: "/admin/ajax/moderation/hotel/disallow/",
    beforeSend: function (request) {
      request.setRequestHeader('X-CSRFToken', getCookie('csrftoken'))
    },
    success: function (request) {
      popup_create('Запрещена модерация объекта', request.hotel_name, [
        {
          name: 'Закрыть',
          type: 'reload'
        }
      ])
    }
  })
}

function allow_hotel(param) {
  $.ajax({
    method: 'POST',
    data: param,
    url: "/admin/ajax/moderation/hotel/allow/",
    beforeSend: function (request) {
      request.setRequestHeader('X-CSRFToken', getCookie('csrftoken'))
    },
    success: function (request) {
      popup_create('Объект прошёл модерацию', request.hotel_name, [
        {
          name: 'Закрыть',
          type: 'reload'
        }
      ])
    }
  })
}

function user_fun_action(type, id) {
  if (type == "login") {
    location.href = `/admin/ajax/auth/user/?user_id=${id}`
  }
  if (type == "open_chat") {
    location.href = `/admin/redirect/open_user_chat/?user_id=${id}`
  }
  if (type == "edit_user") {
    location.href = `/django_admin/user/user/${id}/change/`
  }
  if (type == "user_financial_transactions") {
    location.href = `/admin/page/user/financial_transactions/?user_id=${id}`
  }
}


function reset_record_all() {
  let keys = Object.keys(moder_works).reverse()
  keys.forEach((key, index) => {
    initial_creation_record(index, key)
    reset_record(key)
  })
}

function initial_creation_record(index, id) {
  let tr = $(`
    <tr data-id="${id}">
      <td scope="col" data-type-col="select">
      ${index + 1}
      </td>
      <td scope="col" data-type-col="staff">
        <div class="list">
        </div>
      </td>
      <td scope="col" data-type-col="hotels">
        <div class="list">
        </div>
      </td>
      <td scope="col" data-type-col="contacts">
        <div class="list">
        </div>
      </td>
      <td scope="col" data-type-col="notes">
        <div class="list">
        </div>
      </td>
      <td scope="col"
        data-type-col="work_status">

        <div class="list">
          <span class="value"></span>
          <span class="text"></span>
        </div>


      </td>
      <td scope="col" data-type-col="profile">
        <div class="list">
          <div class="item" data-cell="fio">
            <span class="name">ФИО</span>
            <span class="value"></span>
          </div>
          <div class="item" data-cell="email">
            <span class="name">Почта</span>
            <span class="value"></span>
          </div>
          <div class="item" data-cell="phone">
            <span class="name">Телефон</span>
            <span class="value"></span>
          </div>
        </div>
      </td>
      <td scope="col" data-type-col="reminders">
        <div class="list">
        </div>
      </td>
      <td scope="col" data-type-col="status">
        <div class="list">
        </div>
      </td>
    </tr>
    `)

  $("tbody").append(tr)
}


function submit_change(id) {

  param = moder_works[id]

  $.ajax({
    url: "/admin/ajax/moderator_office/save/",
    type: "POST",
    dataType: 'json',
    contentType: 'application/json',
    data: JSON.stringify(param),
    headers: {
      "X-CSRFToken": getCookie('csrftoken')
    },
    success: function (response) {

      moder_works[response.obj.id] = response.obj


      moder_works[response.obj.id]["reminders"].forEach((item) => {
        if (item.status == "active") {
          addReminder(item.value, item.datetime * 1000);
        }
      });

      reset_record(response.obj.id)
    }
  });
}

function reset_record(id) {
  let tr = $(`tr[data-id="${id}"]`)

  obj = moder_works[id]




  // Персонал
  tr.find(`[data-type-col="staff"] .list`).html(`
    <div class="item" data-id="${obj['staff']['id']}">
      <span class="value">(${obj['staff']['id']}) ${obj['staff']['name']}</span>
  </div>
  `)


  // ФИО, почта, Телефон

  tr.find(`[data-cell="fio"] .value`).text(obj["user"]["fio"]["full"])
  tr.find(`[data-cell="email"] .value`).text(obj["user"]["email"]["value"])
  tr.find(`[data-cell="phone"] .value`).text(obj["user"]["phone"]["value"])

  if (obj["user"]["email"]["status"])
    tr.find(`[data-cell="email"] .value`).addClass("active")
  else
    tr.find(`[data-cell="email"] .value`).addClass("notactive")

  if (obj["user"]["phone"]["status"])
    tr.find(`[data-cell="phone"] .value`).addClass("active")
  else
    tr.find(`[data-cell="phone"] .value`).addClass("notactive")

  // Отели

  tr.find(`[data-type-col="hotels"] .list`).empty()

  for (key in obj["hotels"]) {
    let hotel = obj["hotels"][key]

    let el = $(`
        <div class="item" data-id="${hotel['id']}">
          <span class="name">${hotel['name']}</span>
          <span class="status" style="color: ${hotel['status']['color']}">${hotel['status']['text']}</span>
        </div>
      `)

    tr.find(`[data-type-col="hotels"] .list`).append(el)
  }



  // Контактные данные
  tr.find(`[data-type-col="contacts"] .list`).empty()

  for (key in obj["contacts"]) {
    let contact = obj["contacts"][key]

    let el = $(`
        <div class="item ${contact['status']}">
          <span class="name">${contact['name']}</span>
          <span class="value">${contact['value']}</span>
        </div>
      `)

    tr.find(`[data-type-col="contacts"] .list`).append(el)
  }

  // Комментарий

  tr.find(`[data-type-col="notes"] .list`).empty()

  for (key in obj["notes"]) {
    let note = obj["notes"][key]

    let el = $(`
        <div class="item ${note['status']}">
          <span class="name" data-time="${note.datetime}" data-format-time>${note.datetime}</span>
          <span class="value">${note['value']}</span>
        </div>
      `)

    tr.find(`[data-type-col="notes"] .list`).append(el)
  }


  // Аккаунт передан
  if (obj.param.status == "transferred")
    tr.find(`[data-type-col="work_status"] .list .value`).text("Да").css("color", "#00d200")

  if (obj.param.status == "refused")
    tr.find(`[data-type-col="work_status"] .list .value`).text("Отказался").css("color", "red")

  if (obj.param.status == "at_work")
    tr.find(`[data-type-col="work_status"] .list .value`).text("В работе").css("color", "#053aff")

  if (obj.param.status == "client_account")
    tr.find(`[data-type-col="work_status"] .list .value`).text("Аккаунт клиента").css("color", "#C59C16")


  tr.find(`[data-type-col="work_status"] .list .text`).text(obj.param.note)






  // Статусы

  tr.find(`[data-type-col="status"] .list`).empty()

  for (key in obj["status"]) {
    let status = obj["status"][key]

    let el = $(`
        <div class="item" data-status="${status.value}">
          <span class="name" data-time="${status.datetime}" data-format-time>${status.datetime}</span>
          <span class="value">${status.value}</span>
        </div>
      `)

    tr.find(`[data-type-col="status"] .list`).append(el)
  }



  // Календарь напоминаний

  tr.find(`[data-type-col="reminders"] .list`).empty()

  for (key in obj["reminders"]) {
    let reminder = obj["reminders"][key]

    let el = $(`
        <div class="item ${reminder.status}">
          <span class="name" data-time="${reminder.datetime}" data-format-time>${reminder.datetime}</span>
          <span class="value">${reminder.value}</span>
        </div>
      `)

    tr.find(`[data-type-col="reminders"] .list`).append(el)
  }




  updateElementsFormatTimestamp()
}

$(".toolbar").hide()

$("body").on("click", `td[data-type-col="select"]`, function() {
  $(this).toggleClass("selected")
  let count = $(`td[data-type-col="select"].selected`).length
  if (count > 0) {
    $(".toolbar").show()
  }
  else {
    $(".toolbar").hide()
  }

  $(".toolbar .value").text(count)
})

$('[long-press]').on("mousedown touchstart", function () {
  let button = $(this)
  let funcName = $(button).attr('data-funcName');
  let orig_color = $(button).attr('data-orig-color');

  if (!orig_color) {
    orig_color = "white"
  }

  let gradient_color = $(button).attr('data-gradient-color');
  $(this).attr('data-seconds-passed', 0); // хранение таймера
  let timer_interval = setInterval(function () {
    timer_seconds_passed = parseFloat($(button).attr('data-seconds-passed'));
    max_time = parseFloat($(button).attr('data-max-time'));
    timer_seconds_passed += 0.1
    $(button).attr('data-seconds-passed', timer_seconds_passed)
    procent = Math.round((timer_seconds_passed / max_time) * 100)
    $(button).css('background', `linear-gradient(90deg, ${gradient_color} ${procent}%, ${orig_color} ${procent + 0.1}%)`);
    if (timer_seconds_passed >= max_time) {
      $(button).removeAttr('data-seconds-passed');
      $(button).removeAttr('data-timer-interval');
      clearInterval(timer_interval);
      let param = $(button).attr('data-param')
      if (param) {
        window[funcName](param);
      }
      else {
        window[funcName]();
      }
    }
  }, 100);
  $(this).attr('data-timer-interval', timer_interval); // хранение интервала
});

$('[long-press]').on('mouseup mouseout touchend touchcancel', function () {
  let timer = $(this).attr('data-timer-interval');
  clearInterval(timer);
  $(this).removeAttr('data-seconds-passed');
  $(this).removeAttr('data-timer-interval');
  let orig_color = $(this).attr('data-orig-color');
  if (orig_color) {
    $(this).css('background', orig_color);
  }
  else {
    $(this).css('background', 'white');
  }
});

function toolbar_transfer() {
  let dataIds = $(`td[data-type-col="select"].selected`).map(function() {return $(this).parent().attr('data-id')}).get();


  param = {
    "ids": dataIds,
    "user_id": $(".toolbar select").val(),
  }


  $.ajax({
    url: "/admin/moderwork/api/move/item/",
    type: "POST",
    dataType: 'json',
    contentType: 'application/json',
    data: JSON.stringify(param),
    headers: {
      "X-CSRFToken": getCookie('csrftoken')
    },
    success: function (response) {
      get_moder_works()
      $(`td[data-type-col="select"].selected`).removeClass("selected")
      $(".toolbar").hide()
    }
  });

}