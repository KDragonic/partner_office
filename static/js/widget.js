// Находим элемент <script> по его src атрибуту
var scriptElement = document.querySelector('script[src^="/static/js/widget.js"]');

if (scriptElement) {
  var src = scriptElement.src;
  var queryString = src.split('?')[1];
  var domain = window.location.hostname; // Получаем домен текущего сайта
}

// Создаем родительский div элемент для виджета
var widgetContainer = document.createElement("div");
widgetContainer.classList.add("widget-container");
widgetContainer.setAttribute("widget-type", "directions_for_hotels");


// Создаем заголовок h2 элемент
var widgetHeader = document.createElement("h2");
widgetHeader.classList.add("widget-header");
widgetHeader.textContent = "Направления для отелей";

// Создаем абзац p элемент
var widgetText = document.createElement("p");
widgetText.classList.add("widget-text");
widgetText.textContent = "В этих популярных местах вы точно найдете что-то для себя";

// Создаем список ul элемент
var widgetList = document.createElement("div");
widgetList.classList.add("widget-list");

// Создаем каждый li элемент внутри списка
var cities = [
  { name: "Москва", count: "3533", imgSrc: "/static/img/city/moscow.jpg", href: `http://127.0.0.1:8000/rw/?${queryString}&site=${domain}&next=/hotel/search/russia/moscow/` },
  { name: `Санкт-Петербург`, count: `3656`, imgSrc: `/static/img/city/saint_petersburg.jpg`, href: `http://127.0.0.1:8000/rw/?${queryString}&site=${domain}&next=/hotel/search/russia/saint-petersburg/` },
  { name: `Казань`, count: `499`, imgSrc: `/static/img/city/kazan.jpg`, href: `http://127.0.0.1:8000/rw/?${queryString}&site=${domain}&next=/hotel/search/russia/kazan/` },
  { name: `Сочи`, count: `1108`, imgSrc: `/static/img/city/sochi.jpg`, href: `http://127.0.0.1:8000/rw/?${queryString}&site=${domain}&next=/hotel/search/russia/sochi/` }
];

cities.forEach(function(city) {
  var linkElement = document.createElement("a");
  linkElement.classList.add("widget-list__item");
  linkElement.setAttribute("href", city.href);

  var imageContainer = document.createElement("div");
  imageContainer.classList.add("widget-image");

  var pictureElement = document.createElement("picture");

  var imgSource = document.createElement("source");
  imgSource.setAttribute("type", "image/webp");

  var imageElement = document.createElement("img");
  imageElement.setAttribute("src", city.imgSrc);
  imageElement.setAttribute("alt", "");

  pictureElement.appendChild(imgSource);
  pictureElement.appendChild(imageElement);
  imageContainer.appendChild(pictureElement);

  var infoContainer = document.createElement("div");
  infoContainer.classList.add("widget-info");

  var nameElement = document.createElement("div");
  nameElement.classList.add("widget-info__name");
  nameElement.textContent = city.name;

  var countElement = document.createElement("div");
  countElement.classList.add("widget-info__count");
  countElement.textContent = city.count + " вариантов";

  infoContainer.appendChild(nameElement);
  infoContainer.appendChild(countElement);

  linkElement.appendChild(imageContainer);
  linkElement.appendChild(infoContainer);
  widgetList.appendChild(linkElement);
});

// Добавляем дочерние элементы в родительский div элемент
widgetContainer.appendChild(widgetHeader);
widgetContainer.appendChild(widgetText);
widgetContainer.appendChild(widgetList);

// Вставляем созданный элемент перед найденным элементом <script>
scriptElement.parentNode.insertBefore(widgetContainer, scriptElement);

var headElement = document.head;

var linkElement = document.createElement("link");
linkElement.rel = "stylesheet";
linkElement.type = "text/css";
linkElement.href = "/static/css/widget.css";

headElement.appendChild(linkElement);