markers = []
map = null
r_circle = null
geoObjects = []
clusterer = null

hotels_map_dict_id = {}
map_mode = "list"


setInterval(() => {
  if ($(".inner-content__main > .sidebar-map").length > 0) {
    if ($("#mode-switcher .list-mode.active").length > 0) {
      $("#mode-switcher .list-mode").removeClass("active")
      $("#mode-switcher .map-mode").addClass("active")
    }
  }

  if ($(".sidebar-content > .sidebar-map").length > 0) {
    if ($("#mode-switcher .map-mode.active").length > 0) {
      $("#mode-switcher .list-mode").addClass("active")
      $("#mode-switcher .map-mode").removeClass("active")
    }
  }
}, 200);

function init_map() {
  map_coordinates_start = $("#hotel_map").attr("data-coord-start").split(", ").map(parseFloat);

  map = new ymaps.Map('hotel_map', {
    center: map_coordinates_start,
    zoom: 9,
    behaviors: ['default', 'scrollZoom']
  }, {
    suppressMapOpenBlock: true,
    yandexMapDisablePoiInteractivity: true,
  });

  map.controls.remove('trafficControl')
  map.controls.remove('fullscreenControl')

  // map.controls.remove('geolocationControl')
  map.controls.remove('searchControl')

  clusterer = new ymaps.Clusterer({
    preset: 'islands#orangeClusterIcons',
    hasBalloon: false,
    hasHint: false,
    groupByCoordinates: false,
    clusterDisableClickZoom: false,
    clusterHideIconOnBalloonOpen: false,
    geoObjectHideIconOnBalloonOpen: false,
    gridSize: 64,
    maxZoom: 14,
    minClusterSize: 3,
  });

  map.geoObjects.add(clusterer);

  $("#mode-switcher .list-mode").click(function () {
    if (map != null && clusterer != null) {
      setFullMap(false)
      map_mode = "list"
      $(this).addClass("active");
      $(".map-mode").removeClass("active");
      $(".leaflet-container").removeClass("big_map");

      $("#popup_with_the_hotel").remove()
      $(`.card-hotel__item[data-card-type="map_card"]`).remove()
    }
  });

  $("#mode-switcher .map-mode").click(function () {
    if (map != null && clusterer != null) {
      setFullMap(true)

      map_mode = "full"

      $(this).addClass("active");
      $(".list-mode").removeClass("active");
      $(".leaflet-container").addClass("big_map");

      $("#popup_with_the_hotel").remove()
      $(`.card-hotel__item[data-card-type="map_card"]`).remove()
    }
  });
}


ymaps.ready(function () {
  init_map()
});


is_set_post_map = false


select_marker = null


function reset_scale_map() {
  if (map != null && clusterer != null) {
    map.setBounds(clusterer.getBounds(), {
      checkZoomRange: true
    });
    is_set_post_map = true
  }
}

function set_map_data(hotels_map, map_setting) {
  ymaps.ready(function () {
    const urlParams = new URLSearchParams(window.location.search);
    const paramsString = urlParams.toString();

    hotels_map_dict_id = []

    markersByCoords = {}

    hotels_map.forEach((hotel, index) => {
      hotel_coordinates = [parseFloat(hotel["coordinates"][0]), parseFloat(hotel["coordinates"][1])]

      if (hotel_coordinates != null) {
        let key = hotel_coordinates[0] + ';' + hotel_coordinates[1];
        if (!markersByCoords[key]) {
          markersByCoords[key] = [];
        }
        markersByCoords[key].push(hotel);
      }
    });

    index = 0

    geoObjects = []

    clusterer.removeAll()

    for (let key in markersByCoords) {
      let markers = markersByCoords[key];
      if (markers.length > 1) {
        // Находим центр группы
        let centerLat = 0; let centerLng = 0;
        for (let marker of markers) {
          centerLat += parseFloat(marker.coordinates[0]);
          centerLng += parseFloat(marker.coordinates[1]);
        }

        centerLat /= markers.length;
        centerLng /= markers.length;

        // Задаем радиус распределения
        const radius = 0.0001 * (markers.length / 10);

        // Распределяем каждую метку
        // по кругу относительно центра
        for (let i = 0; i < markers.length; i++) {
          let angle = i / markers.length * Math.PI * 2;
          markers[i].coordinates[0] = centerLat + radius * Math.sin(angle);
          markers[i].coordinates[1] = centerLng + radius * Math.cos(angle);
        }
      }

      for (let hotel of markers) {

        let hotel_name = hotel["name"]
        let hotel_min_price = hotel["min_price"]
        let hotel_id = hotel["id"]

        let coordinates = hotel["coordinates"]

        let min_price_one = Math.ceil(hotel['min_price'] / differenceInDays)

        geoObjects[index] = new ymaps.Placemark(coordinates, {
          iconContent: `${min_price_one} ₽`,
          hintContent: `${hotel_name}`,
          hotel_id: hotel_id,
          hotel_name: hotel_name,
          hotel_min_price: hotel_min_price,
        }, {
          preset: 'islands#orangeStretchyIcon',
        });

        geoObjects[index].events.add('click', function (e) {
          let target = e.get('target');
          let id = target.properties.get("hotel_id")

          if (select_marker) {
            select_marker.options.set('preset', 'islands#orangeStretchyIcon');
          }

          select_marker = target
          select_marker.options.set('preset', 'islands#blueStretchyIcon');

          show_popup_with_the_hotel(id)
        })

        hotels_map_dict_id[hotel_id] = hotel

        index += 1
      }
    }

    clusterer.add(geoObjects);

    if (!is_set_post_map) {
      map.setBounds(clusterer.getBounds(), {
        checkZoomRange: true
      });
      is_set_post_map = true
    }
  });
}

function setFullMap(mode) {
  hotel_map_elem = $("#hotel_map")
  if (mode) {
    //скрыть элементы и перенести #hotel_map
    $(".inner-content__main > *").hide();
    hotel_map_elem.prependTo(".inner-content__main");
    hotel_map_elem.css({ "height": "87vh" });
    map.container.fitToViewport();
    reset_scale_map()
  } else {
    //показать элементы и переместить #hotel_map обратно
    hotel_map_elem.prependTo(".sidebar-content.js-filter-range");
    $(".inner-content__main > *").show();
    hotel_map_elem.css({ "height": "268px" });
    map.container.fitToViewport();
    reset_scale_map()
  }
}


function create_html_popup_with_the_hotel(id) {

  let hotel = hotels_map_dict_id[id]

  imgs_html = ``
  hotel["imgs"].forEach(element => {
    imgs_html += `<img src="${element}" alt="">`
  });

  $("#popup_with_the_hotel").remove()


	const queryString = window.location.search;

  let slide_style = ""
  if ($("body").width() < 1024) {
    slide_style = "display: flex; width: 100%; overflow: auto;"
  }

  let min_price_one = Math.ceil(hotel['min_price'] / differenceInDays)

  let el = `
  <div id="popup_with_the_hotel" data-hotel-id=${hotel['id']}>
      <div class="popup_with_the_hotel_body">
      <div class="handle"></div>
      <div class="slider" style="${slide_style}">
        ${imgs_html}
      </div>

      <a href="/hotel/${hotel['id']}/${queryString}" style="color: black" class="name">
          ${hotel["name"]}
      </a>
      <a href="/hotel/${hotel['id']}/${queryString}" class="address">
          <svg xmlns="http://www.w3.org/2000/svg" width="13" height="15" viewBox="0 0 13 15" fill="none">
          <g clip-path="url(#clip0_16_210)">
              <path d="M1.84198 1.91281C3.02133 0.688059 4.62087 0 6.28871 0C7.95658 0 9.55608 0.688059 10.7354 1.91281C11.9148 3.13756 12.5774 4.79869 12.5774 6.53075C12.5774 8.26279 11.9148 9.92393 10.7354 11.1487L9.87812 12.0292C9.24618 12.6728 8.42646 13.5008 7.41823 14.5134C7.11524 14.8176 6.71022 14.9877 6.28871 14.9877C5.8672 14.9877 5.46218 14.8176 5.15915 14.5134L2.63787 11.9662C2.32082 11.6429 2.05576 11.3707 1.84198 11.1487C1.25801 10.5423 0.79477 9.82236 0.478719 9.03C0.162669 8.23764 0 7.38843 0 6.53075C0 5.67311 0.162669 4.82387 0.478719 4.03152C0.79477 3.23917 1.25801 2.51924 1.84198 1.91281ZM9.96912 2.70784C8.99282 1.69415 7.66877 1.12474 6.2882 1.12488C4.90763 1.12501 3.58366 1.6947 2.60754 2.70859C1.63143 3.72249 1.08313 5.09756 1.08326 6.53129C1.0834 7.965 1.63196 9.33993 2.60826 10.3536L3.68148 11.4547C4.42283 12.2069 5.16624 12.957 5.91171 13.7048C6.01273 13.8063 6.14779 13.8631 6.28835 13.8631C6.42891 13.8631 6.56397 13.8063 6.66499 13.7048L9.11618 11.2297C9.45562 10.8839 9.73946 10.5921 9.9684 10.3536C10.9445 9.33993 11.4929 7.96507 11.4929 6.5315C11.4929 5.09793 10.9445 3.72306 9.9684 2.70934L9.96912 2.70784ZM6.28871 4.48617C6.57343 4.48617 6.85536 4.54441 7.11841 4.65756C7.38147 4.77071 7.62046 4.93656 7.82181 5.14564C8.0231 5.35472 8.18285 5.60294 8.29176 5.87611C8.40074 6.14929 8.45679 6.44208 8.45679 6.73776C8.45679 7.03344 8.40074 7.32621 8.29176 7.59943C8.18285 7.87257 8.0231 8.12079 7.82181 8.32986C7.62046 8.53893 7.38147 8.70479 7.11841 8.81793C6.85536 8.93114 6.57343 8.98936 6.28871 8.98936C5.72064 8.97857 5.17934 8.73664 4.78126 8.31564C4.3832 7.89464 4.16017 7.32821 4.16017 6.73814C4.16017 6.14809 4.3832 5.58163 4.78126 5.16061C5.17934 4.7396 5.72064 4.49769 6.28871 4.48692V4.48617ZM6.28871 5.61121C6.14626 5.61121 6.00519 5.64036 5.87358 5.69697C5.74197 5.75359 5.62238 5.83656 5.52166 5.94117C5.42092 6.04579 5.34102 6.16997 5.28651 6.30665C5.23199 6.44333 5.20393 6.58982 5.20393 6.73776C5.20393 6.8857 5.23199 7.03219 5.28651 7.16886C5.34102 7.30557 5.42092 7.42971 5.52166 7.53436C5.62238 7.63893 5.74197 7.72193 5.87358 7.77857C6.00519 7.83514 6.14626 7.86429 6.28871 7.86429C6.57632 7.86429 6.85214 7.74564 7.05551 7.53443C7.25884 7.32329 7.3731 7.03681 7.3731 6.73814C7.3731 6.43946 7.25884 6.15301 7.05551 5.94181C6.85214 5.73061 6.57632 5.61196 6.28871 5.61196V5.61121Z" fill="#FC7201" />
          </g>
          <defs>
              <clipPath id="clip0_16_210">
              <rect width="13" height="15" fill="white" />
              </clipPath>
          </defs>
          </svg>

          <span class="value">${hotel["address"]}</span>

      </a>
      <a href="/hotel/${hotel['id']}/${queryString}" class="price">
          От ${min_price_one} ₽ за ночь
      </a>
      <span class="reating">
          <div class="value">${hotel['rating_stat']}</div>
          <div class="text">
          <span class="type">${hotel['rating_stat_text']}</span>
          <span class="count">${hotel['reviews_amount']} отзывов</span>
          </div>
      </span>
      <div class="favorite_icon c_point off" data-hotel-id=${hotel['id']}>
          <img width="19" height="19" src="/static/img/favorite_icon_off.png" class="off" alt="">
          <img width="19" height="19" src="/static/img/favorite_icon_on.png" class="on" alt="">
      </div>
      </div>
  </div>
  `

  return el;
}

get_favorite()


$("body").on("click", " .favorite_icon", function () {
  let hotel_id = $(this).data("hotel-id")
  $.ajax({
    method: "POST",
    data: { "hotel": hotel_id },
    url: "/ajax/ajax_toggle_favorite_hotel/",
    beforeSend: function (request) {
      request.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    },
    success: function (request) {
      get_favorite()
    }
  });
  $(this).toggleClass("off")
  $(this).toggleClass("on")
})


function get_favorite() {
  $.ajax({
    url: '/ajax/ajax_get_favorite_hotel/',
    method: 'GET',
    dataType: 'json',
    success: function (response) {
      // Записать значения списка избранных в глобальную переменную
      window.favorites = response.favs
      reset_favorite_icon()
    },
    error: function (xhr, status, error) {
    }
  })
}

function show_popup_with_the_hotel(id) {

  let map_mode_list = $("#mode-switcher .list-mode").hasClass("active")

  $("#popup_with_the_hotel").remove()
  $(`.card-hotel__item[data-card-type="map_card"]`).remove()

  if (map_mode_list) {
    let hotel_map_obj = hotels_map_dict_id[id]
    let card = {
      "stars_text": "★".repeat(hotel_map_obj["stars"]),
      "stars": hotel_map_obj["stars"],
      "id": hotel_map_obj["id"],
      "name": hotel_map_obj["name"],
      "rating_stat": hotel_map_obj["rating_stat"],
      "rating_stat_text": hotel_map_obj["rating_stat_text"],
      "address": hotel_map_obj["address"],
      "imgs": hotel_map_obj["imgs"],
      "min_price": hotel_map_obj["min_price"],
    }

    let elem = gen_card_hotel_to_list(card, "map_card")
    $("#card-hotel").prepend(elem)

    $("img[data-src]").map(function () {
      $(this).attr("src", $(this).data("src"))
    })
  }
  else {
    $(".sidebar-map").append(function () {
      let el = $(create_html_popup_with_the_hotel(id))
      return el;
    })

    reset_favorite_icon()


    $(".sidebar-map").css("overflow", "hidden")
    $("#popup_with_the_hotel").draggable({
      axis: "y",
      drag: function (event, ui) {
        console.log(ui.position)

        let max_top = $(".sidebar-map").height() - $("#popup_with_the_hotel").height()
        let min_top = $(".sidebar-map").height() - 40

        // ui.position.top = max_top - нижная граница карточки к нижней границе карты

        if (ui.position.top <= max_top) {
          ui.position.top = max_top
        }

        else if (ui.position.top >= min_top) {
          ui.position.top = min_top
        }
      },
      stop: function (event, ui) {

        let max_top = $(".sidebar-map").height() - $("#popup_with_the_hotel").height()
        let min_top = $(".sidebar-map").height() - 40

        let mixing_point = (max_top + min_top) / 2

        if (ui.position.top <= mixing_point) {
          ui.position.top = max_top;
          $(this).animate({ "top": `${max_top}px` }, "fast");
        }
        else {
          ui.position.top = min_top;
          $(this).animate({ "top": `${min_top}px` }, "fast");
        }
      }
    });

    init_popup_with_the_hotel_body = false

  }
}


init_popup_with_the_hotel_body = false

setInterval(function () {
  if ($(".popup_with_the_hotel_body .slider").length != 0 && !init_popup_with_the_hotel_body) {
    init_popup_with_the_hotel_body = true
    if ($("body").width() < 1024) {

    }
    else {
      $(".popup_with_the_hotel_body .slider").slick({
        // arrows: false,
        dots: false,
        infinite: true,
        // swipe: false,
        centerMode: true,
        variableWidth: true
      });

      $(".popup_with_the_hotel_body .slider").on("click", function() {
        $(".popup_with_the_hotel_body .slider").slick("slickNext");
      });
    }
  }
}, 100)


function reset_favorite_icon() {
  $(".favorite_icon").map(function () {
    let id = $(this).data("hotel-id")

    if (window.favorites.includes(id)) {
      $(this).removeClass("off").addClass("on")
    }
  })
}
