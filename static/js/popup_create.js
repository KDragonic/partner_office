// popup_create(
//   "Заголовок",
//   "Текст",
//   [
//     { type: "close", name: "Закрыть" },
//     { type: "use-inputs", name: "Применить" }
//   ],
//   [
//     [
//         { type: "text", "label": "Имя", val: "Денис", name: "name" },
//         { type: "email", "label": "Почта", name: "email" },
//     ],
//     [
//         { type: "date", "label": "Дата", name: "date" }
//     ],
//     [
//         { type: "text", "label": "A", name: "text_a" },
//         { type: "text", "label": "Б", name: "text_b" },
//         { type: "text", "label": "С", name: "text_c" },
//     ]
//   ]
// );


/**
 * Функция popup_create создает всплывающее окно с заголовком, текстом, кнопками и дополнительными
 * входными данными и прикрепляет его к телу HTML-документа.
 * @param title - Заголовок всплывающего окна.
 * @param text - Параметр text представляет собой строку, которая представляет содержимое или
 * сообщение, отображаемое во всплывающем окне.
 * @param [buttons] - Массив объектов, представляющих кнопки, отображаемые во всплывающем окне. Каждый
 * объект должен иметь следующие свойства:
 * @param [inputss] - Параметр inputss представляет собой массив объектов, которые определяют поля
 * ввода для всплывающего окна. Каждый объект в массиве представляет собой раздел полей ввода. Каждый
 * раздел может содержать одно или несколько полей ввода.
 * @param [style] - Параметр style — это необязательный параметр, который позволяет настроить внешний
 * вид всплывающего окна. Он принимает строковое значение, представляющее стили CSS, которые вы хотите
 * применить к всплывающему окну.
 */
function popup_create(title, text, buttons = [], inputss = [], style = "") {
  overlay_popup = $(`<div class="overlay_popup"></div>`)
  popup = $(`<div class="info_popup" data-style='${style}'>
              <span class="title popup-title">${title}</span>
              <span class="popup-text">${text}</span>
              <section class="popup_inputss"></section>
              <section class="popup_buttons"></section>
            </div>`)

  if (buttons.length == 0) {
    buttons = [
      { type: "close", name: "Закрыть" },
    ]
  }
  if (inputss != null) {
    inputss.forEach(inputs => {
      inputs_elem = $(`<section class="popup_inputs"></section>`)
      inputs.forEach(input => {
        if (input.type == "hidden") {
          html = `<input type="hidden" value="${input.val ?? ''}" name="${input.name ?? ''}" />`
        }
        else if (input.type == "textarea") {
          html = `<label style="width: 100%;">
            <span>${input.label}</span>
            <textarea class="input" placeholder="${input.ph ?? ''}" name="${input.name ?? ''}" />${input.val ?? ''}</textarea>
          </label>`
        }
        else if (input.type == "select") {
          html = `<label>
            <span>${input.label}</span>
            <select class="input" name="${input.name ?? ''}">`

            input.val.forEach(element => {
              let key = element[0]
              let value = element[1]
              html += `<option  value="${key}">${value}</option>`
            });


            html += `</select>
          </label>`
        }
        else {
          html = `<label>
            <span>${input.label}</span>
            <input type="${input.type}" value="${input.val ?? ''}" class="input" placeholder="${input.ph ?? ''}" name="${input.name ?? ''}" />
          </label>`
        }
        input_elem = $(html)

        if ("setting" in input) {
          if ("max" in input.setting) {
            $(input_elem).find("input").attr("max", input.setting.max);
          }
          if ("min" in input.setting) {
            $(input_elem).find("input").attr("min", input.setting.min);
          }
        }
        inputs_elem.append(input_elem);
      });
      console.log(inputs_elem)
      $(popup).find(".popup_inputss").append(inputs_elem)
    });
  }
  if (buttons != null) {
    id_button = Math.random().toString(36).substring(2, 10)

    buttons.forEach(button => {
      button_elem = $(`<button class="button" data-popup-button="${button.type}" data-id-button="${id_button}">${button.name}</button>`)

      if ("color" in button) {
        $(button_elem).attr("data-color", button.color)
      }


      if ("style" in button) {

        if (typeof button.style === "string") {
          button.style = [button.style];
        } else if (Array.isArray(button.style) === false) {
          throw new TypeError("Свойство style должно быть строкой или массивом");
        }

        if (button.style.includes("full")) {
          $(button_elem).css("width", "100%");
        }

        if (button.style.includes("50%")) {
          $(button_elem).css("width", "calc(50% - 5px / 2)");
        }

        if (button.style.includes("disabled")) {
          $(button_elem).prop("disabled", true);
          $(button_elem).css({
            "pointer-events": "none",
            "opacity": "0.5",
          });
          $(button_elem).off("click");
        }
      }

      undefined_type = true
      $(popup).find(".popup_buttons").append(button_elem);

      if (button.type == "use-inputs") {
        $(button_elem).click(function () {
          let input_vals = {}
          $(popup).find(".input, input").each(function () {
            let name = $(this).prop("name")
            let val = $(this).val()
            input_vals[name] = val
          });
          button.fun.apply(null, [input_vals])
          popup.remove();
          overlay_popup.remove();
          undefined_type = false
        })
      }

      if (button.type == "link") {
        $(button_elem).click(function () {
          if (button.param[1] == 0) {
            location.href = button.param[0]
          }
          else if (button.param[1] == 1) {
            window.open(button.param[0], '_blank');
          }
        })
      }

      if (button.type == "send-inputs") {
        $(button_elem).click(function () {
          let input_vals = {}
          $(popup).find(".input, input").each(function () {
            let name = $(this).prop("name")
            let val = $(this).val()
            input_vals[name] = val
          });
          button.fun.apply(null, [input_vals])
        })
        undefined_type = false
      }

      if (undefined_type == true || button.type == "action") {
        if (button.fun) {
          $(button_elem).click(function () {
            button.fun.apply(null, button.param)
          })
        }
      }
    });
  }

  $("body").append(overlay_popup);
  $("body").append(popup);

  $(popup).find("[data-popup-button='close']").click(function () {
    $(".info_popup").remove();
    $(".overlay_popup").remove();
  });

  $(popup).find("[data-popup-button='reload']").click(function () {
    location.reload()
  });

  $(popup).find("[data-popup-button='close_window']").click(function () {
    window.close()
  });

}

function htmlPopupCreate(html) {
  // <div class="html_popup">
  //   <span class="title popup-text"
  //     style=" font-size: 31px; ">Название</span>
  //   <span class="popup-text"
  //     style="max-width: 354px;font-size: 20px;text-align: center;">Текст</span>
  //   <a href="${url}" style="font-size: 20px;" class="button">Перейти в чат</a>
  // </div>
  overlay_popup = $(`<div class="overlay_popup"></div>`)
  popup = $(html)
  $("body").append(overlay_popup);
  $("body").append(popup);

  // Обработчик нажатия на кнопку закрытия
  $("popup").find(".close").click(function () {
    popup.remove();
    overlay_popup.remove();
  });
}

function popup_load_create(title = "Ожидание") {
  var overlay_popup = $(`<div class="overlay_popup"></div>`)
  var popup = $(`<div class="info_popup" data-type-popup='loader'>
              <span class="title popup-text" style=" font-size: 31px; ">${title}</span>
              <div class="popup_loader"></div>
            </div>`)

  popup_loader = $(popup).find(".popup_loader")

  $("body").append(overlay_popup);
  $("body").append(popup);
}

function load_start() {
  popup_load_create("Загрузка")
}

function load_end() {
  $(".overlay_popup").remove()
  $(".info_popup[data-type-popup='loader']").remove()
}

function all_popup_close() {
  count_popup = $(".info_popup").length
  $(".overlay_popup").remove()
  $(".info_popup").remove()

  return count_popup
}