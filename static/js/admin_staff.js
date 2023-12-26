const user_type_list = { "owner": "Разрабочик", "admin": "Админ", "moder": "Модератор", "hotel": "Отельник", "client": "Клиент" }


function get_list_user() {
  $.ajax({
    method: 'GET',
    url: "/admin/staff/api/get/list/",
    beforeSend: function (request) {
      request.setRequestHeader('X-CSRFToken', getCookie('csrftoken'))
    },
    success: function (request) {
      users = request.users
      reset_html_cards()
    }
  })
}


function get_user(id) {
  $.ajax({
    method: 'GET',
    url: "/admin/staff/api/get/user/",
    data: {
      "user_id": id,
    },
    beforeSend: function (request) {
      request.setRequestHeader('X-CSRFToken', getCookie('csrftoken'))
    },
    success: function (request) {
      show_popup_request(request)
      user = request
      reset_html_detailed_card()
    },
    error: function (jqXHR, exception) {
      if (jqXHR?.responseJSON) {
        show_popup_request(jqXHR.responseJSON)
      }
    }
  })
}


function show_popup_request(request) {
  if (request?.popup) {
    popup_create(request.popup.title, request.popup.text, [], [], request.popup.type)
  }
}

function reset_html_cards() {
  $("#cards").empty()
  for (const key in users) {
    let user = users[key]
    let el = $(`
      <div class="card card_user" data-id="${user.id}">
        <span class="username">${user.fio}</span>
        <span class="post post_color" data-type="${user.type}">${user.type_text}</span>
      </div>
    `)
    $("#cards").append(el)
  }
}

function reset_html_detailed_card() {

  $(".detailed_card").removeClass("d-none")

  $(".detailed_card #moderworks_list").hide()
  $(".detailed_card #chats_messages_list").hide()

  $(".detailed_card #moderworks_list .grupe").empty()
  $(".detailed_card #chats_messages_list .grupe").empty()
  $(".detailed_card #staff_information .grupe").empty()


  if (user?.moderworks) {

    if (user?.moderworks.length > 0) {
      $(".detailed_card #moderworks_list").show()
    }

    for (key in user?.moderworks) {
      let work = user.moderworks[key]

      let el = $(`
        <div class="item">
          <div class="additional_praramters">${work.user}</div>
        </div>
      `)

      for (hotel_key in work.hotels) {
        let hotel = work.hotels[hotel_key]
        el.append(`<span class="value">${hotel}</span>`)
      }

      if (work.status) {
        el.append(`<span class="value color_status" status="${work.status}>${work.status}</span>`)
      }

      $(".detailed_card #moderworks_list .grupe").append(el)
    }
  }


  if (user?.chats_messages) {

    if (user?.chats_messages.length > 0) {
      $(".detailed_card #chats_messages_list").show()
    }

    for (key in user?.chats_messages) {
      let chat = user.chats_messages[key]

      let additional_praramters_text = ""
      if (chat.chat) {
        additional_praramters_text += chat.chat + " - "
      }

      additional_praramters_text += chat.datetime


      let el = $(`
          <div class="item">
            <div class="additional_praramters">${additional_praramters_text}</div>
          </div>
        `)

      el.append(`<span class="value">${chat.text}</span>`)

      $(".detailed_card #chats_messages_list .grupe").append(el)
    }
  }

  if (user?.user?.additional_info?.staff_information) {
    let items = user?.user?.additional_info?.staff_information.split("\n").map(item => item.trim()).filter(item => item !== "");
    for (key in items) {
      let item = items[key]
      let el = $(`
      <span class="item">${item}</span>
      `)
      $(".detailed_card #staff_information .grupe").append(el)
    }
  }

  if (user?.user) {
    let fio = user.user.lastname + " " + user.user.username + " " + user.user.middlename
    fio = fio.trim()
    $(".detailed_card .left_part .username").text(fio)

    let user_type_text = user_type_list[user.user.user_type]

    $(".detailed_card .left_part .post").text(user_type_text).attr("data-type", user.user.user_type)
  }


  $(".detailed_card .right_part .can_scrolled_base").width($(".detailed_card").width() - $(".detailed_card .left_part").width() - 35)
}

$("#login_from_user").click(function () {
  login_from_user()
});

function login_from_user() {
  let id = user?.user?.id
  if (id) {
    location.href = `/admin/ajax/auth/user/?user_id=${id}`
  }
}


$("#change_the_position").click(() => {

  popup_create("Изменить должность",
    "Выберите одну из должностей можно будет поменять в любое время на другую.",
    [
      {
        "name": 'Изменить',
        "fun": change_the_position_stage_2,
        "type": 'send-inputs',
        "color": "green",
      },
      { type: "close", name: "Отмена", color: "red" },
    ],
    [
      [
        { type: 'select', label: 'Список', val: [["admin", "Админ"], ["moder", "Модератор"], ["hotel", "Отельник"], ["client", "Клиент"]], name: 'user_type' }
      ]
    ],
  )
}
)

function change_the_position_stage_2(param) {
  if (!param) return
  all_popup_close()

  user_type_text = user_type_list[user.user.user_type]
  user_type_text_new = user_type_list[param["user_type"]]

  popup_create("Изменить должность",
    `Вы точно хотите изменить должность ${user_type_text} -> ${user_type_text_new}.`,
    [
      { type: "close", name: "Нет", color: "red" },
      {
        name: 'Да, уверен',
        fun: change_the_position_stage_3,
        param: [param["user_type"]],
        type: 'action',
        color: "green"
      },
    ]
  )
}

function change_the_position_stage_3(new_user_type) {
  user.user.user_type = new_user_type
  ajax_edit_user()
  all_popup_close()
}






$("#change_permission").click(() => {

  permission = ""
  if (Array.isArray(user.user.additional_info.permission) && user.user.additional_info.permission.length === 0) {
    permission = ""; // Если пустой массив, присваиваем пустую строку
  } else if (Array.isArray(user.user.additional_info.permission)) {
    permission = user.user.additional_info.permission.join(", "); // Иначе объединяем элементы массива в строку с разделителем ","
  } else {
    permission = ""; // Если не массив, присваиваем пустую строку
  }

  popup_create("Изменить разрешение",
    `Пропишите новые разрешение через запятую, писок доступных разрешений и их значения:<br>
    <b>supermoderator</b> - Открывает доступ к страницам Статистика и Настройка сайтом<br>
    <b>login_to_moderators</b> - Позволяет поолнительно заходить в аккаунты модераторов<br>
    <b>access_to_staff</b> - Доступ к управлению персоналом (/admin/staff/)<br>
    <b>access_to_moderwork</b> - Доступ к управлению рабочими листами (/admin/moderwork/)
    `,
    [
      {
        "name": 'Изменить',
        "fun": change_permission_stage_2,
        "type": 'send-inputs',
        "color": "green",
      },
      { type: "close", name: "Отмена", color: "red" },
    ],
    [
      [
        { type: 'textarea', label: 'Разрешение', val: permission, name: 'permission'}
      ]
    ],
  )
}
)

function change_permission_stage_2(param) {
  if (!param) return
  all_popup_close()

  permission = ""
  if (Array.isArray(user.user.additional_info.permission) && user.user.additional_info.permission.length === 0) {
    permission = ""; // Если пустой массив, присваиваем пустую строку
  } else if (Array.isArray(user.user.additional_info.permission)) {
    permission = user.user.additional_info.permission.join(", "); // Иначе объединяем элементы массива в строку с разделителем ","
  } else {
    permission = ""; // Если не массив, присваиваем пустую строку
  }

  permission_new = param["permission"]

  popup_create("Изменить разрешение",
    `Вы точно хотите изменить разрешение [${permission}] -> [${permission_new}]`,
    [
      { type: "close", name: "Нет", color: "red" },
      {
        name: 'Да, уверен',
        fun: change_permission_stage_3,
        param: [permission_new],
        type: 'action',
        color: "green"
      },
    ]
  )
}


function change_permission_stage_3(permission_new) {
  user.user.additional_info.permission = permission_new
  ajax_edit_user()
  all_popup_close()
}















$("#change_staff_information").click(() => {

  popup_create("Изменить основную информацию",
    ``,
    [
      {
        "name": 'Изменить',
        "fun": change_staff_information_stage_2,
        "type": 'send-inputs',
        "color": "green",
      },
      { type: "close", name: "Отмена", color: "red" },
    ],
    [
      [
        { type: 'textarea', label: 'Основная информация', val: user.user.additional_info.staff_information, name: 'staff_information'}
      ]
    ],
  )
}
)

function change_staff_information_stage_2(param) {
  if (!param) return
  all_popup_close()

  staff_information_new = param["staff_information"]

  popup_create("Изменить основную информацию",
    `Вы точно хотите изменить`,
    [
      { type: "close", name: "Нет", color: "red" },
      {
        name: 'Да, уверен',
        fun: change_staff_information_stage_3,
        param: [staff_information_new],
        type: 'action',
        color: "green"
      },
    ]
  )
}


function change_staff_information_stage_3(staff_information_new) {
  user.user.additional_info.staff_information = staff_information_new
  ajax_edit_user()
  all_popup_close()
}
















function ajax_edit_user() {
  $.ajax({
    method: 'POST',
    data: JSON.stringify(user),
    contentType: "application/json",
    dataType: "json",
    url: "/admin/staff/api/edit/profile/",
    beforeSend: function (request) {
      request.setRequestHeader('X-CSRFToken', getCookie('csrftoken'))
    },
    success: function (request) {
      get_user(user.user.id)
      if (request?.popup) {
        popup_create(request.popup.title, request.popup.text, [], [], request.popup.type)
      }
    }
  })
}


$("#cards").on("click", ".card_user", function () {
  let id = parseInt($(this).attr("data-id"))
  get_user(id)
})

let users = []
$(document).ready(function () {
  get_list_user()

  let urlParams = new URLSearchParams(window.location.search);
  let id_user = urlParams.get('user');
  if (!id_user) {
    return
  }

  get_user(id_user)
});