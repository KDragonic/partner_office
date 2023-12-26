conditions_options = {
  types: {

  },
  methods: {
    "==": {
      label: "Точно",
      help: "<b>Точное совпадения</b>, без учёта регистра",
    },
    "!=": {
      label: "Неравно",
      help: "<b>Поле не равно определенному значению</b>",
    },
    "contains": {
      label: "Содержит",
      help: "<b>Поле содержит определенное значение</b>",
    },
    "startswith": {
      label: "Начинается с",
      help: "<b>Поле начинается с определенного значения</b>",
    },
    "endswith": {
      label: "Заканчивается на",
      help: "<b>Поле заканчивается на определенное значение</b>",
    },
    ">": {
      label: "Больше",
      help: "<b>Больше чем</b>",
    },
    "<": {
      label: "Меньше",
      help: "<b>Меньше чем</b>",
    },
    "range": {
      label: "Диапозон",
      help: "<b>Правильный формат:</b> 46..78",
    },
    "in": {
      label: "Находится в списке",
      help: "<b>Указывать через запятую</b>, без учёта регистра",
    },
  }
}

conditions = []


function load_conditions_options() {
  $.ajax({
    url: "/partner/promocode/get_conditions_options",
    type: "GET",
    success: function (response) {
      conditions_options["types"] = response["conditions_options"]["types"]
    }
  });
}

function new_condition() {
  let el = $(`
      <div class="input-group-cont d-flex flex-column">
        <div class="input-group">
          <select class="form-select" name="type" id=""></select>
          <select class="form-select" name="method" id=""></select>
          <input type="text" name="param" id="" class="form-control" placeholder="Значение">
        </div>

        <small class="text-muted text-input-type"></small>
        <small class="text-muted text-input-method"></small>
      </div>
    `)

  let types = conditions_options["types"]
  let methods = conditions_options["methods"]

  for (type_key in types) {
    el.find(`[name='type']`).append(`<option value='${type_key}'>${types[type_key]['label']}</option>`);
  }

  for (method_key in methods) {
    el.find(`[name='method']`).append(`<option value='${method_key}'>${methods[method_key]['label']}</option>`);
  }

  $("#add_new_conditions").before(el);

  let index = $("section.conditions .input-group-cont").index(el)
  reset_conditions_input(index)
  reset_text_input_method(index)
}

function autoSelectNextOption(selectElement) {
  // Проверка, является ли выбранный вариант заблокированным
  if (selectElement.find(':selected').is(':disabled')) {
    // Перебор остальных вариантов выбора
    selectElement.find('option').each(function () {
      const option = $(this);

      // Проверка, является ли вариант доступным
      if (!option.is(':disabled')) {
        // Выбор доступного варианта
        selectElement.val(option.val());
        return false; // Прерывание цикла перебора
      }
    });
  }
}

function reset_conditions_input(index) {
  let input_group_cont = $("section.conditions .input-group-cont").eq(index)
  let type_value = $(input_group_cont).find(`select[name='type']`).val()
  let type = conditions_options["types"][type_value]
  $(input_group_cont).find("select[name='method'] option").map(function () {
    let val = $(this).val()
    if (type["methods"].includes(val))
      $(this).removeAttr("disabled")
    else
      $(this).attr("disabled", true)
  })

  // Проверить после изменения метод всё ещё доступен, если нет выбирает первый доступный
  autoSelectNextOption((input_group_cont).find("select[name='method']"))
  reset_text_input_method(index)

  $(input_group_cont).find(`.text-input-type`).html(type['help']);
}

function reset_text_input_method(index) {
  let input_group_cont = $("section.conditions .input-group-cont").eq(index)
  let method_value = $(input_group_cont).find(`select[name='method']`).val()
  let method = conditions_options["methods"][method_value]
  input_group_cont.find(`.text-input-method`).html(method['help']);
}

$(document).ready(function () {
  $('.promocodes .list .promocodes-item .button-menu').click(function () {
    $(this).toggleClass('active')
    $(this).parent().find('.promocode-menu').toggleClass('show')
  })

  $("section.conditions").on("change", ".input-group-cont select[name='type']", function () {
    let index = $("section.conditions .input-group-cont").index($(this).parents(".input-group-cont"))
    reset_conditions_input(index)
  });

  $("section.conditions").on("change", ".input-group-cont select[name='method']", function () {
    let index = $("section.conditions .input-group-cont").index($(this).parents(".input-group-cont"))
    reset_text_input_method(index)
  });


  $('#add_new_conditions').click(function () {
    new_condition()
  })

  load_conditions_options()

});
