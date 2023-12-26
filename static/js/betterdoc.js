$(document).ready(function () {
  var methods = {
    init: function (params) {
      var defaults = {
        min: 0,
        max: 99,
        name: null,
        list: [],
        exts: [],
      };


      var options = $.extend({}, defaults, params);
      if (options.exts.length <= 0) {
        throw new Error("Должно: длина [exts] > 0, список расширений файлов не должен быть пустым");
      }

      if (options.min < 0) {
        throw new Error("Должно: [min] >= 0");
      }

      if (!(options.min <= options.max)) {
        throw new Error(`Должно: [min] <= [max]`);
      }

      if (this.length != 1)
        throw new Error(`Должно: 1 DOM элемент`);


      var elthis = this
      var getting_a_photo = false
      // инициализируем лишь единожды
      if (!this.data('betterdoc')) {

        let id = Math.random().toString(36).substring(7)

        options.id = id

        // закинем настройки в реестр data
        this.data('betterdoc', options);

        this.attr("data-id", id)

        if (options.name)
          if (options.min > 0) this.append(`<span class="name">${options.name}*</span>`)
          else this.append(`<span class="name">${options.name}</span>`)

        let extsStr = options.exts.map((ext) => { return '.' + ext }).join(', ');

        this.append(`
          <div class="files">
              <label class="img_add">
                <input type="file" name="betterdoc_${id}[]" accept="${extsStr}" multiple>
                <span>+</span>
              </label>
            </div>
          `)


        if (options.min == options.max) {
          this.append(`<div class="discription">Нужно выбрать ${options.min} файлов</div>`)
        }
        else {
          if (options.max == 99) {
            this.append(`<div class="discription">Нужно выбрать от ${options.min} файлов (включительно)</div>`)
          }
          else {
            this.append(`<div class="discription">Нужно выбрать ${options.min}-${options.max} файлов</div>`)
          }
        }

        // Кнопка удалить
        $(this).on("click", ".remove", function (event) {
          var img_elem = $(event.target).parents(".img_elem")
          var id = $(img_elem).data("id")
          options.list = options.list.filter(item => item !== id);
          elthis.data('betterdoc', options);
          img_elem.remove()
        })

        // Событие при выборе файла
        $(this).find("input").on('change.betterdoc', function (event) {
          options = elthis.data('betterdoc')
          var files = event.target.files;
          var formData = new FormData();
          for (var i = 0; i < files.length; i++) {
            formData.append('file[]', files[i]);
          }
          if (getting_a_photo) {
            return
          }
          getting_a_photo = true
          $.ajax({
            url: '/utils/add_not_linked_doc/',
            type: 'POST',
            data: formData,
            headers: {
              "X-CSRFToken": getCookie('csrftoken'),
            },
            contentType: false,
            processData: false,
            success: function (data) {
              data.id_list.forEach(obj => {
                let ext = obj.url.split('.').pop().toLowerCase()
                if (['jpg', 'jpeg', 'png', 'gif', 'svg'].includes(ext)) {
                  var html = `<div class="img_elem" data-id="${obj.id}"><img src="${obj.url}"><div class="remove">✖</div></div>`
                  var elem = $(html)
                  $(elthis).find(".files").find(".img_add").before(elem)
                }
                else {
                  var html = `
                  <div class="img_elem" data-id="${obj.id}">
                    <div class="unable_to_display">
                      <a href="${obj.url}" target="_blank" class="ext">${ext}</a>
                    <div class="remove">✖</div>
                  </div>
                  `
                  var elem = $(html)
                  $(elthis).find(".files").find(".img_add").before(elem)
                }
                options.list.push(obj.id)
              });
              getting_a_photo = false
              elthis.data('betterdoc', options);
            },
            error: function (jqXHR, textStatus, errorThrown) {
              console.log('Error: ' + errorThrown);
              getting_a_photo = false
            }
          });
        });
      }
      return this;
    },
    len: function () {
      var options = $(this).data('betterdoc');
      return options.list.length
    },
    add: function (obj) {
      var options = $(this).data('betterdoc');
      let ext = obj.url.split('.').pop().toLowerCase()
      if (['jpg', 'jpeg', 'png', 'gif', 'svg'].includes(ext)) {
        var html = `<div class="img_elem" data-id="${obj.id}"><img src="${obj.url}"><div class="remove">✖</div></div>`
        var elem = $(html)
        $(this).find(".files").find(".img_add").before(elem)
      }
      else {
        var html = `
        <div class="img_elem" data-id="${obj.id}">
          <div class="unable_to_display">
            <a href="${obj.url}" target="_blank" class="ext">${ext}</a>
          <div class="remove">✖</div>
        </div>
        `
        var elem = $(html)
        $(this).find(".files").find(".img_add").before(elem)
      }
      options.list.push(obj.id)
      $(this).data('betterdoc', options);
      return true
    },
    reset: function () {
      var options = $(this).data('betterdoc');
      $(this).find(".files .img_elem").remove()
      options.list = []
      $(this).data('betterdoc', options);
      return true
    },
    getlist: function () {
      var options = $(this).data('betterdoc');
      return options.list
    },
    check_the_pictures: function () {
      var options = $(this).data('betterdoc');
      options.list = []
      $(this).find(".files .img_elem").map(function (index, elem) {
        options.list.push($(elem).data("id"))
      })
      $(this).data('betterdoc', options);
      return this
    },
    valid: function () {
      var options = $(this).data('betterdoc');
      var isValid = true
      $(`.error_input.input_file_error`).remove()

      if (options.list.length < options.min) {
        if ($(`.error_input.input_file_error[data-type="min"]`).length == 0) {
          $(`.label_input_file_${options.id}`).append(`<span class="error_input input_file_error" data-type="min">Не менее ${options.min} файлов</span>`)
        }
        isValid = false
      }
      if (options.list.length > options.max) {
        if ($(`.error_input.input_file_error[data-type="max"]`).length == 0) {
          $(".label_input_file_${options.id}").append(`<span class="error_input input_file_error" data-type="max">Не больше ${options.max} файлов</span>`)
        }
        isValid = false
      }
      return isValid
    }
  }


  $.fn.betterdoc = function (method) {
    if (methods[method]) { return methods[method].apply(this, Array.prototype.slice.call(arguments, 1)) }
    else if (typeof method === 'object' || !method) { return methods.init.apply(this, arguments) }
    else { $.error('Метод "' + method + '" в плагине не найден') }
  };
})
