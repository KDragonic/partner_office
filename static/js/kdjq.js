// jQuery-подобная функция для создания KDJQ плагина



(function ($) {
  jQuery.fn.kdjq = function (settings) {
    var config = {
      source: {},
      form: {
        values: {},
      }
    };

    if (settings) jQuery.extend(config, settings);

    this.each(function () {
      $element = $(this)


      // ===== Вспомогательные методы =====

      // Генерация случайной строки
      function generateRandomString() {
        let randomString = '';

        for (let i = 0; i < 6; i++) {
          randomString += 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'.charAt(Math.floor(Math.random() * 62));
        }

        return randomString;
      }

      // Форматирование числа
      function formatNumber(number, format) {
        if (format === 'compact') {
          if (number >= 1000000) {
            number = (number / 1000000).toFixed(2) + ' млн.';
          } else if (number >= 1000) {
            number = (number / 1000).toFixed(2) + ' тыс.';
          } else {
            number = number.toLocaleString('ru-RU');
          }
          return number;
        } else if (format === 'exponential' && number > 999) {
          return number.toExponential(3);
        } else {
          return number.toLocaleString('ru-RU');
        }
      }


      // ==== Обрабочики ====

      // Обработчик клика по ячейке
      function handleCellClick() {
        const $cell = $(this);
        const isOpen = $cell.hasClass('open');
        const $row = $cell.parents('.kdjq_table--row');
        const colspanCount = $row.find('.kdjq_table--row--cell').length;
        let $detailCell = $row.next('.kdjq_table--row-detail');
        $cell.parent().find(`.kdjq_table--row--cell.open[kdjq-cell-detailed]`).removeClass("open")

        if ($detailCell.length === 1) {
          $detailCell.remove();
        }

        if (isOpen == false) {
          $cell.addClass('open');

          const rowId = $row.attr('kdjq-id');
          const cellId = $cell.attr('kdjq-cell-id');
          const expandedRaw = config.source.list[rowId][cellId]?.expanded;
          let expanded;

          if (expandedRaw?.link) expanded = config.source.links[expandedRaw.link];
          else expanded = expandedRaw;

          if (expanded?.list) {
            let html = '';

            expanded.list.forEach(obj => {
              html += `<div class="item d-flex gap-1"><span class="name" style="font-weight: 600!important;">${obj.name}:</span><span class="value">${obj.value}</span></div>`;
            });

            const $rowDetail = $('<tr class="kdjq_table--row kdjq_table--row-detail">').append(
              $(`<td colspan="${colspanCount}" class="kdjq_table--row--cell" kdjq-role="cell" kdjq-cell-type="detail">`).append(
                $(`<div class="d-flex flex-column align-items-start px-3">`).append(html)
              )
            );

            $rowDetail.insertAfter($row);
          }
        }
      }

      // Обработчик изменения типа записи
      function handleInputChange() {
        let name = $(this).attr("name")
        $input = $(this).parents(`[kdjq-role="input"]`)
        let type_input = $input.attr("kdjq-input-type")

        if (name in config.source.form.values) {
          // Декоративно, потом удалить
          let str_name = $(this).parents(`[kdjq-role="input"]`).find("label").text()

          if (type_input == "select") {
            let old_value = config.source.form.values[name];
            let new_value = $(this).val()

            let str_old_value = $(this).find(`option[value="${old_value}"]`).text()
            let str_new_value = $(this).find(`option[value="${new_value}"]`).text()
            config.source.form.values[name] = $(this).val();
            console.log(`Значения поля [${str_name}] изменено "${str_old_value}" => "${str_new_value}"`)
          }
          else if (type_input == "date-range") {
            let name_from;
            let name_in;

            let is_from = name.endsWith("_from")
            if (is_from) {
              name_to = name.replace("from", "to")
              name_from = name
            }
            else {
              name_from = name.replace("to", "from")
              name_to = name
            }

            str_old_date_from = config.source.form.values[name_from];
            str_old_date_to = config.source.form.values[name_to];

            config.source.form.values[name] = $(this).val();

            str_new_value = $(this).val()
            if (is_from) {
              console.log(`Значения поля [${str_name}] изменено "${str_old_date_from} - ${str_old_date_to}" => "${str_new_value} - ${str_old_date_to}"`)
            }
            else {
              console.log(`Значения поля [${str_name}] изменено "${str_old_date_from} - ${str_old_date_to}" => "${str_old_date_from} - ${str_new_value}"`)
            }
          }
          else {
            let old_value = config.source.form.values[name];
            let new_value = $(this).val()

            config.source.form.values[name] = $(this).val();
            console.log(`Значения поля [${str_name}] изменено "${old_value}" => "${new_value}"`)
          }
        }

        if (["record_type", "grouping"].includes(name)) {
          resetTable();
        }
      }

      // ===== Перезапуск =====

      // Сброс статистики
      function resetStat() {
        resetForm()
        resetTable()
      }

      function resetForm() {
        $form = $element.find(`[kdjq-role="form-option"]`)
        $button_apply = $form.find(`button[button-event="apply"]`)

        $form.find(":input").not("button").remove()

        for (const key in config.source.form.inputs) {
          if (Object.hasOwnProperty.call(config.source.form.inputs, key)) {
            let obj = config.source.form.inputs[key];

            let $input = null

            if (obj.type == "date-range") {
              $input = $(`<div class="col flex-grow-0" style="min-width: 300px;" kdjq-role="input" kdjq-input-type="${obj.type}">
                <label class="form-label">${obj.label}</label>
                <div class="input-group">
                  <input type="date" class="form-control" name="${obj.name}_from" placeholder="${obj.placeholder}"/>
                  <span class="input-group-text" style="background-color: transparent;" id="prefixId">-</span>
                  <input type="date" class="form-control" name="${obj.name}_to" placeholder="${obj.placeholder}" />
                </div>
              </div>`)

              config.source.form.values[`${obj.name}_from`] = null
              config.source.form.values[`${obj.name}_to`] = null
            }
            else if (obj.type == "select")  {
              $input = $(`
              <div class="col flex-grow-0" style="min-width: 300px;" kdjq-role="input" kdjq-input-type="${obj.type}">
                <label class="form-label">${obj.label}</label>
                <select class="form-control" name="${obj.name}">
                </select>
              </div>
              `)

              for (option of obj.options) {
                $input.find("select").append($(`<option value="${option.value}">${option.label}</option>`))
              }

              config.source.form.values[`${obj.name}`] = obj.options[0].value
            }
            else {
              $input = $(`<div class="col flex-grow-0" style="min-width: 300px;" kdjq-role="input" kdjq-input-type="${obj.type}">
                <label for="input_hotel_type" class="form-label">${obj.label}</label>
                <input type="text" class="form-control" name="${obj.name}" placeholder="${obj.placeholder}" />
              </div>`)
            }

            // console.log(`${key} =>`, obj, $input)

            $($input).insertBefore($button_apply)
          }
        }

      }

      function resetTable() {
        const $table = $element.find('[kdjq-role="table"]');
        const $header = $table.find('[kdjq-role="header"]');
        const $body = $table.find('[kdjq-role="body"]');


        // Очистить строки которые уже есть
        $body.empty();
        $header.empty();


        let $header_row = $element.data("$header_row")

        if ($header_row === undefined) {
          // Создания шапку для таблицы если её нету в data
          $header_row = $(`<tr class="kdjq_table--row"></td>`)
          config.source.table.fields.forEach((params, index) => {
            let $th = $(`<th class="kdjq_table--row--cell not-bg" kdjq-role="cell" kdjq-cell-id="${params['id']}">${params['name']}</th>`)
            $header_row.append($th)
          });
        }
        $header.append($header_row)



        let $body_row = $element.data("$body_row")

        // Создать шаблон row (tr) и сохранить его если его нету
        if ($body_row === undefined) {
          $body_row = $(`<tr class="kdjq_table--row kdjq_table--row-value"></td>`)
          config.source.table.fields.forEach((params, index) => {

            let $td = $(`<td class="kdjq_table--row--cell kdjq_table--row--cell-value" kdjq-role="cell" kdjq-cell-id="${params['id']}" kdjq-cell-type="${params['type']}">${params['name']}</td>`)

            if (params["format"])
              $td.attr("kdjq-format", params["format"])

            if (params["starts_with"])
              $td.attr("kdjq-cell-starts-with", params["starts_with"])

            if (params["ends_with"])
              $td.attr("kdjq-cell-ends-with", params["ends_with"])

            $body_row.append($td)
          });
        }
        $element.data("$body_row", $body_row)

        /* <th class="kdjq_table--row--cell not-bg" kdjq-cell-id="promo_code" kdjq-role="cell">Промокод</th> */

        const kdjqOptionData = config.source.list;

        kdjqOptionData.forEach((params, index) => {
          let $row_copy = $body_row.clone().attr("kdjq-id", index)

          for (let cell_id in params) {
            let $td = $row_copy.find(`[kdjq-cell-id='${cell_id}']`)
            let value = params[cell_id]["value"]
            $td.attr("value", value)
            if (params[cell_id]?.expanded) {
              $td.attr("kdjq-cell-detailed", '')
            }
          }

          $body.append($row_copy)
        });

        if (config.source.form.values["grouping"] !== "") {
          resetStatTableGrouping()
        }

        resetStatTableCell()
      }

      // Сброс ячеек таблицы статистики
      function resetStatTableCell() {
        const $table = $element.find('[kdjq-role="table"]');
        const $body = $table.find('[kdjq-role="body"]');

        $body.find('.kdjq_table--row--cell-value').each(function() {
          let val = $(this).attr('value');
          let cell_type = $(this).attr('kdjq-cell-type');
          if (cell_type === 'int') val = parseInt(val);

          let starts_with = $(this).attr('kdjq-cell-starts-with') || '';
          let ends_with = $(this).attr('kdjq-cell-ends-with') || '';
          if ($(this).attr('kdjq-format') === 'number') $(this).text(`${starts_with} ${formatNumber(val, config.source.form.values["record_type"])} ${ends_with}`);
          else $(this).text(`${starts_with} ${val} ${ends_with}`);
        });
      }

      function resetStatTableGrouping() {
        const $table = $element.find('[kdjq-role="table"]');
        const $body = $table.find('[kdjq-role="body"]');

        let grouping_id = config.source.form.values["grouping"]
        console.log(`Изменение на просмотор по группам => ${grouping_id}`)

        let grouping = config.source.table.grouping[grouping_id] // Тут будет хранится dict значений с количеством записей
        let field = grouping["field"] // Тут будет хранится dict значений с количеством записей

        const colspanCount = $body.find('.kdjq_table--row').first().find('.kdjq_table--row--cell-value').length;

        for (group of grouping["list"]) {
          let label = group["label"]
          let bg = group["bg"]
          let font_color = group["color"]
          let cell_color = group["cell"]
          $tr = $(`
          <tr class="kdjq_table--row kdjq_table--row-group" style="padding: 2px;">
            <td colspan="${colspanCount}" class="kdjq_table--row--cell" kdjq-role="cell" kdjq-cell-type="group" style="background-color: ${bg}; color: ${font_color};">${label}</td>
          </tr>
          `)

          $rows = $body.find('.kdjq_table--row-value').filter(function () {
            let cell_value = $(this).find(`[kdjq-cell-id="${field}"]`).attr("value")
            return label == cell_value
          })
          $rows.find(".kdjq_table--row--cell").css("background-color", cell_color)

          $body.append($tr)
          $tr.after($rows);
        }

        $(`[kdjq-cell-id="${field}"]`).remove()

      }


      // ==== Другое =====

      // Перезапуск (Общий)
      function restart() {
        // Таблица
        if ($element.hasClass('kdjq_stat')) {
          resetStat();
        }
      }

      // Инициализация плагина
      function init() {
        let init_html = `<div class="d-flex flex-wrap gap-2 kdjq-form-option align-items-end" kdjq-role="form-option"> <button class="btn text-white" button-event="apply" style="background-color: #FC7201; height: min-content; box-shadow: 4px 4px 16px 0px rgba(0, 0, 0, 0.25);"> <span>Применить</span> <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 22 22" fill="none"> <g clip-path="url(#clip0_35_15139)"> <path d="M21.7989 20.8192L15.1188 14.0982C16.3639 12.607 17.1143 10.6886 17.1143 8.59375C17.1143 3.84759 13.2667 0 8.52051 0C3.77435 0 -0.0732422 3.84759 -0.0732422 8.59375C-0.0732422 13.3399 3.77435 17.1875 8.52051 17.1875C10.6769 17.1875 12.6465 16.3914 14.1556 15.0789L20.8264 21.7917C21.0949 22.0602 21.5304 22.0602 21.7989 21.7917C22.067 21.5232 22.067 21.088 21.7989 20.8192H21.7989ZM8.52051 15.8238C4.52751 15.8238 1.29041 12.5868 1.29041 8.59375C1.29041 4.60075 4.52751 1.36366 8.52051 1.36366C12.5135 1.36366 15.7506 4.60075 15.7506 8.59375C15.7506 12.5868 12.5135 15.8238 8.52051 15.8238Z" fill="white" /> </g> <defs> <clipPath id="clip0_35_15139"> <rect width="22" height="22" fill="white" /> </clipPath> </defs> </svg> </button> <button class="btn" button-event="download" style="height: min-content; box-shadow: 4px 4px 16px 0px rgba(0, 0, 0, 0.25);"> <span>Скачать</span> <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"> <rect width="24" height="24" fill="white" /> <path d="M19 9H15V3H9V9H5L12 16L19 9ZM5 18V20H19V18H5Z" fill="black" /> </svg> </button> </div> <table class="kdjq_table" kdjq-role="table"> <thead kdjq-role="header"></thead> <tbody class="flex-column" kdjq-role="body"></tbody> </table>`

        $element.html(init_html)
        $element.addClass("d-flex gap-2 flex-column")
        $element.attr("kdjq", "")

        $element.on('click', '.kdjq_table--row--cell[kdjq-cell-detailed]', handleCellClick);
        $element.on('change', '.kdjq-form-option :input', handleInputChange);


        config.source.form["values"] = {}

        restart();
      }

      // Вызываем инициализацию для каждого элемента
      init();
    });

    return this;
  };
})(jQuery);