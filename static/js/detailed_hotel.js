function createSlider(label, end) {
  let valueElement = $(`.rating_selection .item.${label} .text .value`);
  let sliderElement = $(`.rating_selection .item.${label} .progress`);

  sliderValues[label] = end

  sliderElement.slider({
    value: end,
    orientation: "horizontal",
    max: end,
    range: "min",
    animate: true,
    slide: function( event, ui ) {
      $(valueElement).html(ui.value)
    },
    stop: function( event, ui ) {
      sliderValues[label] = ui.value;
    }
  });
}

sliderValues = {}

createSlider('purity', 10);
createSlider('location', 10);
createSlider('food', 10);
createSlider('price_quality_ratio', 10);
createSlider('number_quality', 10);
createSlider('service', 10);


$(".view_all_amenities").click(function() {
  if ($(window).width() < 1024) {
    $(".hotel_servers_grupe").append($(".zen-roomspage-detailed-amenities-multi-list-wrapper"))
  }
  else {

    $('html, body').animate({
        scrollTop: $(".zen-roomspage-detailed-amenities-multi-list-wrapper").offset().top
    }, 'fast');
  }
})

$(document).ready(function() {
  $('.send_review_button').click(function(e) {
    e.preventDefault();

    var form = $('.popup_body');

    // получаем данные формы и добавляем в них значения из слайдера
    var form_data = new FormData();


    form.find('input:not([type="file"]), select, textarea').each(function() {
      form_data.append($(this).attr('name'), $(this).val());
    });

    var photo_inputs_files = $('.input_photo_for_review_label input')[0].files;
    for (var i = 0; i < photo_inputs_files.length; i++) {
      var photo_input = photo_inputs_files[i];
      form_data.append(`files`, photo_input, photo_input.name);
    }

    form_data.append('purity', sliderValues["purity"]);
    form_data.append('location', sliderValues["location"]);
    form_data.append('food', sliderValues["food"]);
    form_data.append('price_quality_ratio', sliderValues["price_quality_ratio"]);
    form_data.append('number_quality', sliderValues["number_quality"]);
    form_data.append('service', sliderValues["service"]);

    // отправляем данные на сервер с помощью AJAX запроса
    $.ajax({
      url: '/hotel/create_review/',
      type: 'POST',
      data: form_data,
      contentType: false,
      processData: false,
      beforeSend: function (request) {
        request.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
      },
      success: function(response) {
        console.log(response);
        location.reload()
      },
      error: function(xhr, status, error) {
        console.log(xhr.responseText);
        alert('Ошибка при отправке отзыва!');
      }
    });
  });
});


$(document).on("click", ".button_select_food_rate", function() {
  var offset = $(this).offset();
  var left = offset.left;
  var top = offset.top + $(this).height() + 10;

  let rc_id = $(this).parents(".filter-result").data("rc")


  $(`.list_select_food_rate[data-rc='${rc_id}']`).toggleClass("hidden")

  $(`.list_select_food_rate[data-rc='${rc_id}']`).css({
    left: left,
    top: top
  });
});

$(document).on("change", ".list_select_food_rate input", function() {
  let rc_id = $(this).parents(".list_select_food_rate").data("rc")
  let inputs = $(this).parents(".list_select_food_rate").find("input")


  inputs.prop("checked", false)
  $(this).prop("checked", true)

  let val = $(this).val()
  let rc = $(`.filter-result[data-rc='${rc_id}']`)
  let final_price = $(rc).data("final-price")

  let new_price = final_price + parseInt(val)

  $(rc).find(".span_final_price .value").text(new_price)

  $(rc).data("current-price", new_price)
  $(`.list_select_food_rate[data-rc='${rc_id}']`).addClass("hidden")
  set_cpmb()
});

$(document).ready(function () {
  $("#grupe_rooms").on("change.select_count", "select.count", function () {
    set_cpmb()
  });
  set_cpmb()
});

function set_cpmb() {
  rooms = []
  cpmb = $(".calculation_of_the_price_of_a_multi_booking")
  $(cpmb).html("")
  sum_count_room = 0
  rcs_list = []
  sum_count_price = 0

  $("#grupe_rooms > .filter-result").map(function () {
    let name_room = $(this).find(".filter-result__name").text()
    let count = parseInt($(this).find("select.count").val())
    let select_count = $(this).find("select.count")

    if (count == 0) {
      $(this).find("select.count").removeClass("nofirstselect")
    }
    else {
      $(this).find("select.count").addClass("nofirstselect")
    }

    room_price = parseInt($(this).data("current-price"))

    room_price_one = parseInt($(this).attr("data-final-price-one"))
    room_price_orig = parseInt($(this).attr("data-final-price"))

    count_day = Math.round(room_price_orig / room_price_one)

    beds = $(this).find(".filter-result__text").text()

    sum_count_room += count
    full_price = count * room_price
    sum_count_price += full_price

    let rc_id = $(this).data("rc")

    select_food_rate_name = "nf"

    let select_food_rate = $(`.list_select_food_rate[data-rc='${rc_id}'] input:checked`)
    if (select_food_rate.length > 0) {
      select_food_rate_name = select_food_rate.attr("name")
    }

    if (count > 0) {
      rcs_list.push($(this).data("rc") + "." + count + "." + select_food_rate_name)
      var elem = $(`
      <div class="item"
        style=" display: flex; flex-direction: row; align-items: center; justify-content: space-between;">
        <span class="name"
          style="display: flex;flex-direction: column; margin-right: 21px;">
          <span class="name"
            style="font-size: 18px;font-weight: 600;">${name_room}</span>
          <span class="beds"
            style=" color: #7a7a7a; max-width: 334px; ">${beds}</span>
        </span>
        <span class="price"
          style=" font-size: 22px; display: flex; max-width: 676px; width: 100%; justify-content: space-between; ">
          <span class="room_price">${room_price} ₽ <span style="font-size: 14px;">(${room_price_one} * ${count_day})</span></span>
          <span>*</span>
          <span class="count">${count}</span>
          <span>=</span>
          <span class="full_price">${full_price} ₽</span>
          <div class="remove cross display-mob"></div>
        </span>
        <div class="remove cross display-pc"></div>
      </div>
      `)

      $(elem).find(".remove").click(function() {
        select_count.val(0)
        set_cpmb()
      })

      $(cpmb).append(elem)
    }

    $("#popup_calculation_of_the_price_of_a_multi_booking").remove()

    if (rcs_list.length) {
      $("body").append(`
      <div id="popup_calculation_of_the_price_of_a_multi_booking">
        <div class="text">
          <span class="count">Выбрано: ${rcs_list.length}</span>
          <span class="price">Цена: ${sum_count_price} ₽</span>
        </div>
        <a href="#cotpoamb" class="bulochka_in_popup button">Подробнее</a>
      </div>
      `)
    }

  });

  url_to_book = `/hotel/room/to_book/`

  data = {
    "rcs": rcs_list.join("-")
  }

  qp = getQueryParams()

  data = { ...data, ...qp };
  qs = getQueryString(data)

  url_to_book += "?" + qs

  if (sum_count_room == 0) {
    cpmb.addClass("empty")
    $(cpmb).append(`
    <div class="text_center" style="text-align: center; font-size: 22px;">
      Выберите количество номеров
    </div>
    `)
  }
  else {
    cpmb.removeClass("empty")
    $(cpmb).append(`
    <div class="final_panel_price">
      <div class="count">Выбрано: ${sum_count_room}</div>
      <div class="price">${sum_count_price} ₽</div>
      <a href="${url_to_book}" class="button">Забронировать</a>
    </div>
    `)

    $(".fast_booking_button").attr("href", url_to_book)
  }
}