function close_the_save_form() {
  $(`[data-section="edit_room"]`).addClass("d-none")
}

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

let the_same_type_of_numbers_list = {}


$(`#the_same_type_of_numbers`).on("click", `[data-event="add"]`, function () {
  let $input_with_button_cont = $(this).parents(".input_with_button_cont")
  let name = $input_with_button_cont.find("input").val()
  $input_with_button_cont.find("input").val("")
  if (name) {

    let randomID = Math.random().toString(36).substring(2, 12);

    $input_with_button_cont.before(`
      <label data-id=${randomID} class="input_with_button_cont col-md-12 col-lg-6 col-xl-4" for="">
        <div class="input_with_button">
          <input type="text" placeholder="" data-new="True" value="${name}" />
          <div class="buttons">
            <div class="item red" data-event="remove">Удалить</div>
          </div>
        </div>
      </label>
    `)

    the_same_type_of_numbers_list[randomID] = {
      "type": "new",
      "name": name,
    }
  }
})

$(`#the_same_type_of_numbers`).on("click", `[data-event="remove"]`, function () {
  let $input_with_button_cont = $(this).parents(".input_with_button_cont")
  let id = $input_with_button_cont.data("id")



  delete the_same_type_of_numbers_list[id]

  $input_with_button_cont.remove()

})

$(".edit_room_button").click(function () {
  let id = $(this).parents(".record_card").data("id")
  let newParams = new URLSearchParams(window.location.search);
  newParams.set('rc', id);
  let newUrl = `${window.location.pathname}?${newParams.toString()}`;
  window.history.pushState({}, '', newUrl);

  get_rc_ajax()
})


$(`.record_card[data-id="new"]`).click(function() {
  select_room_id = "new"
  $(`[data-section="edit_room"]`).removeClass("d-none");
  $(`.record_card[data-id="${select_room_id}"]`).parents(".row_crads").after($(`[data-section="edit_room"]`));

  let newParams = new URLSearchParams(window.location.search);
  newParams.set('rc', "new");
  let newUrl = `${window.location.pathname}?${newParams.toString()}`;
  window.history.pushState({}, '', newUrl);

  $("#the_same_type_of_numbers").append(`
  <label class="input_with_button_cont col-md-12 col-lg-6 col-xl-4" for="">
    <div class="input_with_button add_the_same_type_of_numbers_button">
      <input type="text" placeholder="Название" value="" />
      <div class="buttons">
        <div class="item green" data-event="add">Добавить</div>
      </div>
    </div>
  </label>
`)

})



function get_rc_ajax() {
  let urlParams = new URLSearchParams(window.location.search);
  let id_rc = urlParams.get('rc');
  if (!id_rc) {
    return
  }

  data = {
    "rc": id_rc,
  }

  $.ajax({
    method: "GET",
    data: data,
    url: "/profile/hotel/rooms/get/",
    beforeSend: function (request) {
      request.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    },
    success: function (request) {
      Object.entries(request).forEach(([key, value]) => {
        $(`[name="${key}"]`).val(value)
      });

      request.rservice.forEach((value) => {
        $(`[name="rservice[]"][value="${value}"]`).prop("checked", true)
      });

      $(`.beds_label .input_span input`).val(0)

      $("#the_same_type_of_numbers").empty()

      the_same_type_of_numbers_list = {}

      request.rooms.forEach((room) => {


        let randomID = Math.random().toString(36).substring(2, 12);

        $("#the_same_type_of_numbers").append(`
          <label data-id=${randomID} class="input_with_button_cont col-md-12 col-lg-6 col-xl-4" for="">
            <div class="input_with_button">
              <input type="text" placeholder="" data-new="False" value="${room}" disabled />
              <div class="buttons">
                <div class="item red" data-event="remove">Удалить</div>
              </div>
            </div>
          </label>
        `)

        the_same_type_of_numbers_list[randomID] = {
          "type": "exist",
          "name": room,
        }

      });

      $("#the_same_type_of_numbers").append(`
      <label class="input_with_button_cont col-md-12 col-lg-6 col-xl-4" for="">
        <div class="input_with_button add_the_same_type_of_numbers_button">
          <input type="text" placeholder="Название" value="" />
          <div class="buttons">
            <div class="item green" data-event="add">Добавить</div>
          </div>
        </div>
      </label>
    `)

      for (let key in request.beds) {
        val = request.beds[key];
        elem = $(`.beds_label .input_span[data-type-bed="${key}"] input`)
        $(elem).val(val)
      }

      $(`[name*="food_rate_"]`).val("0")
      $(`[name*="food_rate_"]`).parents(".checkbox_text_value").removeClass("selected")

      let food_rate = request.additional_info?.food_rate
      if (food_rate) {
        for (let key in food_rate) {
          let value = food_rate[key]
          $(`[name="food_rate_${key}"]`).val(value)
          $(`[name="food_rate_${key}"]`).parents(".checkbox_text_value").addClass("selected")
        }
      }


      $("#label_input_file_photo_room").multifile("reset")

      files_jq = $("#label_input_file_photo_room").find(".files")
      request.images.forEach(item => {
        item_a = $(`<div class="img_elem" data-id="${item.id}"><img src="${item.url}"><div class="remove">✖</div></div>`)

        $(files_jq).find(".img_add").before(item_a)
      });

      $("#label_input_file_photo_room").multifile("check_the_pictures")

      select_room_id = request.id

      $(`[data-section="edit_room"]`).removeClass("d-none");

      $(`.record_card[data-id="${select_room_id}"]`).parents(".row_crads").after($(`[data-section="edit_room"]`));
    }
  });
}


function remove_room(id) {
  $(`.record_card[data-id="${id}"]`).parents(".row_crads").hide()
  $.ajax({
    method: "POST",
    data: {'rc': id},
    url: "/profile/hotel/rooms/remove/",
    beforeSend: function (request) {
      request.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    },
    success: function (request) {
      $(`.record_card[data-id="${id}"]`).parents(".row_crads").remove()
    },
    error: function() {
      $(`.record_card[data-id="${id}"]`).parents(".row_crads").show()
    }
  });
}

function switch_on_off(id) {
  $.ajax({
    method: "POST",
    data: {'id': id},
    url: "/ajax/form_toggle_eneble_rcategory/",
    beforeSend: function (request) {
      request.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    },
    success: function (request) {
      $(`.record_card[data-id="${id}"]`).find(`[data-funcName="switch_on_off"]`).toggleClass("d-none")
    },
    error: function() {

    }
  });
}

function save_an_entry_simple() {
  save_an_entry("save")
}

function save_an_entry_copy() {
  save_an_entry("copy")
}

function save_an_entry(mode) {
  if (window.FormData === undefined) {
    alert('В вашем браузере FormData не поддерживается')
  } else {

    form_data = new FormData();

    form_data.append('photo_room[]', $(`#label_input_file_photo_room`).multifile("getlist"));

    var selected_rservice = [];
    $('input[name="rservice[]"]:checked').each(function () {
      selected_rservice.push($(this).val());
    });

    let urlParams = new URLSearchParams(window.location.search);
    let rc_id = urlParams.get('rc');

    if (mode != "save") {
      rc_id = mode
    }


    if (!$(`.label_input_file[input-file-name="photo_room"]`).multifile("valid")) {
      return false
    }

    required_fields_filled = true

    $(':input[required]').each(function () {
      if ($(this).val() === '') {
        $(this).css('border-color', 'red');
        required_fields_filled = false
      }
    });

    if (!required_fields_filled) {
      return false
    }

    var beds = {};
    $('.input_span').each(function () {
      var type = $(this).data("type-bed");
      var val = $(this).find('input').val();
      if (val == "" || val == NaN || val == undefined) {
        val = "0"
      }
      beds[type] = parseInt(val);
    });

    beds_string = Object.entries(beds).map(([key, value]) => `${key}=${value}`).join('&');



    if (window.FormData === undefined) {
      alert('В вашем браузере FormData не поддерживается')
    } else {
      form_data = new FormData();

      if (!$(`.label_input_file[input-file-name="photo_room"]`).multifile("valid")) {
        return false
      }

      var selectedrservice = [];
      $('input[name="rservice"]:checked').each(function () {
        selectedrservice.push($(this).val());
      });

      $.map($("#the_same_type_of_numbers input"), function (el, key) {
        $(el)
      });
      form_data.append('id', rc_id);

      let the_same_type_of_numbers_json = JSON.stringify(the_same_type_of_numbers_list);
      form_data.append('the_same_type_of_numbers', the_same_type_of_numbers_json);


      form_data.append('photo_room[]', $(`.label_input_file[input-file-name="photo_room"]`).multifile("getlist"));
      form_data.append("rservice[]", selectedrservice)
      form_data.append("name", $("*[name='name']").val())
      form_data.append("offer_type", $("*[name='offer_type']").val())
      form_data.append("square", $("*[name='square']").val())
      form_data.append("beds", beds_string)
      form_data.append("description_of_the_room", $("*[name='description_of_the_room']").val())
      form_data.append("price_base", $("*[name='price_base']").val())
      form_data.append("min_days", $("*[name='min_days']").val())
      form_data.append("max_adults", $("*[name='max_adults']").val())
      form_data.append("count_room", $("*[name='count_room']").val())
      form_data.append("count_bedrooms", $("*[name='count_bedrooms']").val())
      form_data.append("the_amount_of_the_security_deposit", $("*[name='the_amount_of_the_security_deposit']").val())

      form_data.append("prepayment_for_the_room_before_checkin", $("*[name='prepayment_for_the_room_before_checkin']").val())



      $.each($("[name*='food_rate']"), function (index, el) {
        let name = $(this).attr("name")
        let value = $(this).val()
        let enable = $(this).parents(".checkbox_text_value").hasClass("selected");
        if (enable) {
          form_data.append(name, value)
        }
      });

      close_the_save_form()
      $.ajax({
        method: "POST",
        data: form_data,
        contentType: false,
        processData: false,
        url: "/profile/hotel/rooms/save/",
        beforeSend: function (request) {
          request.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        },
        success: function (request) {
          let record_card = $(`.record_card[data-id="${request.rc.id}"]`)
          record_card.find("icon").attr("src", request.rc.img)
          record_card.find(".name .name").text(request.rc.name)
          record_card.find(".name .price_base").text(request.rc.price_base + " ₽")
          record_card.find(".name .price_base").text(request.rc.price_base + " ₽")
          record_card.find(".max_adults").text("Вместимость: " + request.rc.max_adults)
        }
      });
    }
  }
}

$("[name='food_rate']").keydown(function () {
  let val = $(this).val()
  if (val < 0) {
    $(this).val(0)
  }
  else {
    $(this).val(parseInt(val))
  }
})