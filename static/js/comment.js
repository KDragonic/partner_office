$(".review_grupe").on("click", ".collapse_the_response", function () {
	review_long_text = $(this).parents(".review_long_text")
	if (review_long_text.hasClass("mini")) {
		review_long_text.removeClass("mini")
		$(this).html("Развернуть ответ")
	}
	else {
		review_long_text.addClass("mini")
		$(this).html("Свернуть ответ")
	}
});

$(".review_grupe").on("click", ".hotel_response .view_the_hotel_response", function () {
	hotel_response = $(this).parents(".hotel_response")
	base_hotel_response = hotel_response.find(".base_hotel_response")
	if (hotel_response.hasClass("hide")) {
		hotel_response.removeClass("hide")
		$(this).html("Свернуть ответ отеля")
	}
	else {
		hotel_response.addClass("hide")
		$(this).html("Развернуть ответ отеля")
	}
});

// Функция для получения отзывов и вывода их на страницу
function getReviews(page) {

	let hotelId = window.location.pathname.split('/')[2];

	let sorting_review = $("#sorting_review").val()

	$.ajax({
		type: "GET",
		url: "/hotel/reviews/",
		data: {
			hotel_id: hotelId,
			sort_by: sorting_review,
			page: page
		},
		success: function (response) {
			const fields = ["location", "price_quality_ratio", "purity", "food", "service", "number_quality", "hygiene_products", "wifi_quality"];

			for (const field of fields) {
				const value = response.basic_info[field];
				const percent = value * 10;
				const $item = $(`.overall_rating_2 .item.${field}`);

				$item.find(".progress .value").css("width", `${percent}%`);
				$item.find(".text .value").html(value);
			}


			$(".overall_rating_1 .texts .count_value").html(response.basic_info.count)
			$(".overall_rating_1 .number").html(response.basic_info.overall_rating)
			$(".overall_rating_1 .texts .value").html(response.basic_info.overall_rating_text)


			// Очищаем контейнер для отзывов
			$(".review_grupe").empty();

			// Выводим отзывы на страницу
			for (var i = 0; i < response.results.length; i++) {
				let review = response.results[i];

				let review_item = $(`<div class="review_item">`)

				let basic_info = $(`
				<section class="basic_info">
					<div class="s_block username">
						${review['username']}
					</div>
					<span class="date">
						${review['date']}
					</span>
					<span class="rcategory">
					${review['rcategory']}
					</span>
				</section>
			`)

				let basic_review = $(`<section class="basic_review">`)

				let rating_header = $(`
				<div class="s_block rating_header">
					<div class="value">
						<div class="number">${review['overall_rating']}</div>
						<div class="text">${review['overall_rating_text']}</div>
					</div>
					<div class="text_rating">
					</div>
				</div>
			`)

				if (review["wifi_quality"] != "не пользовались") {
					$(rating_header).find(".text_rating").append(`
					<div class="item">
						<span class="name">Оценка Wi-Fi:</span>
						<span class="value">${review["wifi_quality"]}</span>
					</div>
					`)
				}

				if (review["hygiene_products"] != "не пользовались" || review["hygiene_products"] != "не окалазось набора") {
					$(rating_header).find(".text_rating").append(`
					<div class="item">
						<span class="name">Средства гигиены:</span>
						<span class="value">${review["hygiene_products"]}</span>
					</div>
					`)
				}

				let ratings_progress = $(`
					<section class="s_block ratings_progress">
						<div class="item">
							<div class="progress purity">
								<div class="value" style="width: ${review["purity"] * 10}%;"></div>
							</div>
							<div class="text">
								<span>Чистота</span>
								<span>${review["purity"]}</span>
							</div>
						</div>
						<div class="item">
							<div class="progress location">
								<div class="value" style="width: ${review["location"] * 10}%;"></div>
							</div>
							<div class="text">
								<span>Расположение</span>
								<span>${review["location"]}</span>
							</div>
						</div>
						<div class="item">
							<div class="progress food">
								<div class="value" style="width: ${review["food"] * 10}%;"></div>
							</div>
							<div class="text">
								<span>Питание</span>
								<span>${review["food"]}</span>
							</div>
						</div>
						<div class="item">
							<div class="progress price_quality_ratio">
								<div class="value" style="width: ${review["price_quality_ratio"] * 10}%;"></div>
							</div>
							<div class="text">
								<span>Цена/качество</span>
								<span>${review["price_quality_ratio"]}</span>
							</div>
						</div>
						<div class="item">
							<div class="progress number_quality">
								<div class="value" style="width: ${review["number_quality"] * 10}%;"></div>
							</div>
							<div class="text">
								<span>Номер</span>
								<span>${review["number_quality"]}</span>
							</div>
						</div>
						<div class="item">
							<div class="progress service">
								<div class="value" style="width: ${review["service"] * 10}%;"></div>
							</div>
							<div class="text">
								<span>Обслуживание</span>
								<span>${review["service"]}</span>
							</div>
						</div>
					</section>
				`)


				// Левый
				$(review_item).append(basic_info)


				// Правый
				$(basic_review).append(rating_header)
				$(basic_review).append(ratings_progress)


				if (review['what_is_good_text']) {
					let what_is_good_text = $(`
					<section class="s_block review_long_text what_is_good_text">
					<span class="title">Что было хорошо</span>
					<span class="body_text">${review['what_is_good_text']}</span>
					</section>
				`)

					$(basic_review).append(what_is_good_text)
				}


				if (review['what_is_bad_text']) {
					let what_is_bad_text = $(`
					<section class="s_block review_long_text what_is_bad_text">
					<span class="title">Что было плохо</span>
					<span class="body_text">${review['what_is_bad_text']}</span>
					</section>
				`)

					$(basic_review).append(what_is_bad_text)
				}

				if (review['imgs'].length > 0) {
					let imgs_review = $(`
						<section class="s_block imgs_review">
							<span class="title">Фото от гостя</span>
							<div class="imgs">
							</div>
						</section>
					`)

					review['imgs'].forEach(img => {
						$(imgs_review).find(".imgs").append(`<img src="${img}" alt="">`)
					});

					$(imgs_review).find(".imgs").append(`<button class="all_photos open-popup-review-photos">Все фото</button>`)

					$(basic_review).append(imgs_review)
				}


				if (review['reply']) {
					let reply_hotel_review = $(`
					<section class="hotel_response hide">
						<div class="view_the_hotel_response">
							Развернуть ответ отеля
						</div>

						<div class="s_block base_hotel_response">${review['reply']}</div>
					</section>
					`)

					$(basic_review).append(reply_hotel_review)
				}

				$(review_item).append(basic_review)

				// Карточка отзыва
				$(".review_grupe").append(review_item);
			}
		},
		error: function (error) {
			// console.log(error);
		}
	});
}

$(document).ready(function () {
	var sortBy = 'creation_date'; // Сортировка по дате
	var page = 1; // Номер страницы
	getReviews(page);
});