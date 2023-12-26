let chat_type = null
let count_mess = 0
let chat_id = 0
let isGetMessages = false



$(document).ready(function () {
  $(".chat_types .item").not(".active").click(function () {

    $(".chat_types .item.active").removeClass("active")

    let chat_type = $(this).data("type")
    $(`.chat_types[data-type='${chat_type}']`).addClass("active")

    let newParams = new URLSearchParams(window.location.search);
    newParams.set('chat_type', chat_type);
    let newUrl = `${window.location.pathname}?${newParams.toString()}`;
    window.history.pushState({}, '', newUrl);

    getChats()
  })

  $(".chat_list").on("click", ".chat_item_hotel", function() {
    $(".chat_item_hotel.active").removeClass("active")
    $(this).addClass("active")
    let id = $(this).data("chat-id")

    let newParams = new URLSearchParams(window.location.search);
    newParams.set('chat', id);
    let newUrl = `${window.location.pathname}?${newParams.toString()}`;
    window.history.pushState({}, '', newUrl);

    chat_id = id
    load_chat()
  })

  $("#chat_max").on("click", ".booking_category_button .item", function() {
    $(".booking_category_button .item").removeClass("active")
    $(this).addClass("active")
    let id = $(this).data("chat-id")

    let newParams = new URLSearchParams(window.location.search);
    newParams.set('chat', id);
    let newUrl = `${window.location.pathname}?${newParams.toString()}`;
    window.history.pushState({}, '', newUrl);

    chat_id = id
    load_chat()
  })


  setInterval(function () {
    if (isGetMessages == false) {
        get_messages(true, false);
    }
  }, 5000);

  $(document).on('keydown', 'textarea', function(e) {
    if (e.keyCode == 13) {
      e.preventDefault();
      sendMessages();
    }
  });

  $('#file_input').on('change', function () {
      if ($("#file_input").val()) {
          // файл выбран
          sendMessages();
      }
  });


  $(".send_messages").click(function () {
    sendMessages()
  });

  $('#file_input').on('change', function () {
    if ($("#file_input").val()) {
        // файл выбран
        sendMessages();
    }
  });


  getChats()
  checkChat()
  load_chat()

  $("body").on("click", ".button_prev.show", function () {
    $(".chat_list").removeClass("d-none")
    $("#chat_max").addClass("d-none")
    $(".chat_types_mobil").removeClass("d-none")
    $(".button_prev").removeClass("show")
  });

});


function checkChatType() {
  let urlParams = new URLSearchParams(window.location.search);
  let chatType = urlParams.get('chat_type');
  if (chatType) {
    $(`.chat_types .item[data-type="${chatType}"]`).addClass("active")
    return chatType
  }
  else {
    $(".chat_types .item").first().addClass("active")
    return $(".chat_types .item.active").first().data("type")
  }
}

function checkChat() {
  let urlParams = new URLSearchParams(window.location.search);
  chat_id = urlParams.get('chat');
  if (chat_id) {
    $(`.chat_item_hotel[data-chat-id="${chat_id}"]`).addClass("active")
    return chat_id
  }
  return null
}



function getChats() {
  chat_type = checkChatType()
  $.ajax({
    url: "/chat/get_chats/",
    type: "GET",
    data: {
      chat_type: chat_type
    },
    success: function(response) {
      // Код для обработки успешного ответа от сервера

      reget_chats_list(response.chats)
      checkChat()
    }
  });
}


function reget_chats_list(chats) {
  $(".chat_list .chat_item_hotel").remove()
  chats.forEach(chat => {
    $el = $(`
      <div class="chat_item_hotel" data-chat-id="${chat['id']}">
          <img src="${chat['img']}">
          <span class="chat_user">${chat['title']}</span>
          <span class="chat_title">${chat['text']}</span>
      </div>
    `)

    $(".chat_list").append($el)
  });
}

function load_chat() {
  data = {
      "chat": chat_id,
  }

  $.ajax({
      method: "GET",
      data: data,
      url: "/chat/load/",
      beforeSend: function (request) {
          request.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
      },
      success: function (data) {

          if ($(document).width() < 1000) {
            $(".chat_list").addClass("d-none")
            $("#chat_max").removeClass("d-none")
            $(".chat_types_mobil").addClass("d-none")
            $(".button_prev").addClass("show")
          }


          if (data["chat"].hasOwnProperty('group_booking')) {
            set_button_select_booking(data["chat"]["group_booking"], chat_id)
          }

          get_messages(false, true)
      }
  });
}

function set_button_select_booking(chats_id, select_id) {
  $(".booking_category_button").remove()

  booking_category_button = $(`<div class="booking_category_button" style="position: absolute;font-size: 14px;margin: 5px;margin-right: 25px;display: flex;gap: 7px;flex-direction: row;flex-wrap: wrap;"></div>`)
  $("#chat_max").append(booking_category_button)

  chats_id.forEach((obj) => {
    id = obj["id"]
    name = obj["data"]["booking"]
    if (obj["id"] == select_id) {
      $(booking_category_button).append(`<div data-chat-id="${id}" class="item active">${name}</div>`)
    }
    else {
      $(booking_category_button).append(`<div data-chat-id="${id}" class="item">${name}</div>`)
    }
  })

}

function get_messages(isRestart, new_chat) {
  isGetMessages = true
  data_get = {
      "chat": chat_id,
      "isRestart": isRestart,
  }

  $.ajax({
      method: "GET",
      data: data_get,
      url: "/chat/messages/",
      beforeSend: function (request) {
          request.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
      },
      success: function (data) {
          isGetMessages = false
          if (data.status && data.status == "not_now_messages") {
              console.log("Нету новых сообщений")
          }
          else {
              add_messages_to_html(data.messages, isRestart, new_chat)
          }
      }
  });
}

function add_messages_to_html(messages, isRestart = false, new_chat = false) {

  if (!isRestart && !new_chat && count_mess <= messages.length) {
      return
  }

  count_mess = messages.length

  $("#messages > .media").remove()
  $("#messages > .title-date-messages").remove()
  savedDay = null

  messages.forEach(message => {
      // получаем дату сообщения
      let messageDate = new Date(message.date);
      // получаем день сообщения
      let messageDay = messageDate.getDate();

      // сравниваем дни
      if (messageDay != savedDay) {
          // добавляем дату перед сообщением
          let date = messageDate.toLocaleString('ru-RU', { day: 'numeric', month: 'numeric', year: 'numeric' });
          $("#messages").append(`<p class="title-date-messages text-muted text-center">${date}</p>`)
          // сохраняем текущий день
          savedDay = messageDay;
      }

      if (message.belong == "client") {
          html = $(`<div class="media media-his">
              <div class="media-left media-fix-width">
                  <img class="media-object img-circle"
                  src="/static/img/av_user.png"
              style="max-width:75px;">
              </div>
              <div class="media-right media-fix-width">
              </div>
              <div class="media-body media-body-left">
              <div class="message-body">
                  ${message.text}
              </div>
              </div>
              <div class="message-data-right text-muted">
              ${message.time}
              </div>
          </div>`)
      }
      else if (message.belong == "info") {
          html = $(message.text)
      }
      else if (message.belong == "admin") {
          html = $(`
          <div class="media media-my">
              <div class="media-left message-data-left text-muted">
                  ${message.time}
              </div>
              <div class="media-right media-fix-width">
                  <img class="media-object img-circle" src="/static/img/av_user_ts.png" style="max-width:75px;">
              </div>
              <div class="media-body media-body-right">
                  <div class="message-body">
                      ${message.text}
                  </div>
              </div>
          </div>
          `)
      }
      else if (message.belong == "hotel") {
          html = $(`
          <div class="media media-my">
              <div class="media-left message-data-left text-muted">
                  ${message.time}
              </div>
              <div class="media-right media-fix-width">
                  <img class="media-object img-circle" src="${message.avatar}" style="max-width:75px;">
              </div>
              <div class="media-body media-body-right">
                  <div class="message-body">
                      ${message.text}
                  </div>
              </div>
          </div>
          `)
      }

      if (message.file_url) {
        file = $(`<a class="file_message" href="${message.file_url}">`);
        $(file).attr("target", "_blank");
        $(file).text("Файл")
        $(html).find(".message-body").prepend(file);
      }

      $("#messages").append(html)
  });

  $("#messages").scrollTop($("#messages").scrollTop() + $("#messages").height());
}


function sendMessages() {
  var text = $("#entering_a_message_text").text();
  var file = $("#file_input").prop('files')[0];
  if (text != "" || file) {
      var data_post = new FormData();
      data_post.append("text", text);
      data_post.append("chat", chat_id);
      if (file) {
          var allowedExtensions = /(\.jpg|\.jpeg|\.png|\.bmp)$/i;
          if (!allowedExtensions.exec(file.name)) {
              alert('Допустимы только файлы с расширениями: .jpg, .jpeg, .png, .bmp.');
              return false;
          }
          data_post.append("file", file);
      }

      $("#entering_a_message_text").text("");
      $("#file_input").val("")

      $.ajax({
          method: "POST",
          data: data_post,
          url: "/chat/send/",
          beforeSend: function (request) {
              request.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
          },
          processData: false,
          contentType: false,
          success: function (data) {
              text = $("#entering_a_message_text").text("");
              $("#file_input").val("");
              get_messages(true, false);
          }
      });
  }
}