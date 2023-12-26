hotels = []

function clear_fillter() {
	create_fillter_id()
	window.location.reload()
}

let card_hotel_body = $("#card-hotel")
let count_card_max = 20


$(".filter-select input[type='text']").change(function () {
	create_fillter_id();
	get_hotel_fillter();
})

$(".filter-select select").change(function () {
	create_fillter_id();
	get_hotel_fillter();
})

$(".filter-select input[type='checkbox']").change(function () {
	create_fillter_id();
	get_hotel_fillter();
})

$(`*[name="sorting"]`).change(function () {
	get_hotel_fillter();
})


function getQueryParams() {
	const urlParams = new URLSearchParams(window.location.search);
	const params = {};
	for (let [key, value] of urlParams) {
		params[key] = value;
	}
	return params;
}

fillter_id = null
c_fillter_id = null

function create_fillter_id() {
	fillter_id = Math.floor(Math.random() * (999999 - 99999 + 1) + 99999);

	full_card_grupe = false
	card_hotel_body.html(`<div class="loader">loading</div>`)
	count_card_max = 20
	all_list_hotel = []
	final_max_hotel_count_cur = 0
	hotels_already_exist = []
}

create_fillter_id()

function get_hotel_fillter_ajax() {
	data = {
		"duration_value": duration_value,
		"price_value[]": price_value,
		"fillter_id": fillter_id,
	}

	buildings_list = Array.from($("*[name='building[]']:checked"), item => $(item).val());
	rservices_list = Array.from($("*[name='rservices[]']:checked"), item => $(item).val());
	hservices_list = Array.from($("*[name='hservices[]']:checked"), item => $(item).val());
	additional_criterias_list = Array.from($("*[name='additional_criteria[]']:checked"), item => $(item).val());


	if (buildings_list.length > 0) {
		data["buildings"] = buildings_list
	}
	if (rservices_list.length > 0) {
		data["rservices"] = rservices_list
	}
	if (hservices_list.length > 0) {
		data["hservices"] = hservices_list
	}
	if (additional_criterias_list.length > 0) {
		data["additional_criterias"] = additional_criterias_list
	}

	if($(`*[name="name_hotel"]`).val().length > 0) {
		data["name_hotel"] = $(`*[name="name_hotel"]`).val()
	}

	if($(`*[name="sorting"]`).val() != "not") {
		data["sorting"] = $(`*[name="sorting"]`).val()
	}


	data["count_card_max"] = count_card_max

	qp = getQueryParams()
	data = { ...data, ...qp };

	const slugWithoutParams = window.location.href.split('?')[0].split('#')[0]; // Убираем параметры из ссылки
	const slug = slugWithoutParams.replace('https://turgorodok.ru/hotel/search/', '').replace(/\/$/, '');

	data["slug"] = slug


	all_list_hotel = []

	final_max_hotel_count_cur = 0

	$.ajax({
		method: "GET",
		data: data,
		url: "/hotel/search/fillter/",
		beforeSend: function (request) {
			request.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
		},
		success: function (request) {

			$("#next_card_hotel_loading").remove()

			if (request.fillter_id != fillter_id) {
				return
			}

			if (!request.final_request) {
				$(".h_c_cur_h_c_max_type").html("подбираем варианты")
			}
			else {
				$(".h_c_cur_h_c_max_type").html("доступно")
				final_max_hotel_count_cur = request.hotel_count.cur
			}

			$("#h_c_cur").html(request.hotel_count.cur)
			$("#h_c_max").html(request.hotel_count.max)

			if (request.hotel_count.cur > request.hotel_count.max) {
				$("#h_c_cur").html(request.hotel_count.max)
			}

			hotels = request.hotel

			text_under_price = request.text_price_room


			all_list_hotel = request.hotel
			set_hotel_card(all_list_hotel, request.hotel_count, request.final_request)

			set_map_data(request.hotels_map, request.map_setting)

			if (!request.final_request) {
				get_hotel_fillter_ajax(data)
			}
		}
	});
}

function get_hotel_fillter() {
	$("#card-hotel").html(`<div id="loader_hotels" style=" display: flex; flex-direction: column; align-items: center; "> <svg class="spinner" viewBox="0 0 50 50"> <circle class="path" cx="25" cy="25" r="20" fill="none" stroke-width="5"></circle> </svg> <span class="text" style=" font-size: 20px; margin-top: 20px; ">Подбираем свободные варианты</span> <div>`)

	create_fillter_id()
	first_set_map_data = true
	get_hotel_fillter_ajax();
}

const queryString = window.location.search;
text_under_price = ""

hotels_already_exist = []

function gen_card_hotel_to_list(card, type = "def") {
	if ($(window).width() > 1024) {

		if(hotels_already_exist.includes(card.id)) {
			return
		}

		hotels_already_exist.push(card.id)

		let hotel_top__stars_html = "";
		if (card.stars_text.length > 0) {
			hotel_top__stars_html = `<div class="hotel-top__stars" style="font-size: 27px; height: 36px; margin-top: -14px; color: #FC7201;">${card.stars_text}</div>`
		}

		if (card.apartment_text) {
			apartment_text_html = `
				<span style="color: #828282; font-family: Manrope; font-size: 14px; font-style: normal; font-weight: 400; line-height: 123.6%; display: block;">${card.apartment_text}</span>
			`
		}
		else {
			apartment_text_html = ""
		}


		var elem = $(`
		<li class="card-hotel__item" data-card-type=${type}>
		<div class="card-hotel__img">
			<div class="card_hotel_img_grupe" style="width: 100%; height: 100%;"></div>
			<div class="favorite_icon full c_point off" style="height: 26px; width: 26px;" data-hotel-id=${card.id}>
				<img width="19" height="19" src="/static/img/favorite_icon_off.png" class="off" alt="">
				<img width="19" height="19" src="/static/img/favorite_icon_on.png" class="on" alt="">
			</div>
		</div>
		<div class="card-hotel__body" style="padding: 7px;">
			<div class="hotel-top" style="display: flex; flex-direction: column; justify-content: space-between; height: 100%;">
				<div class="hotel-top__right" style="margin-bottom: 10px; display: flex; flex-direction: column; gap: 6px;">
					<a target="_blank"
						href="/hotel/${card.id}/${queryString}"
						class="hotel-top__title" style="margin-bottom: 0">${card.name}</a>

					${hotel_top__stars_html}
					<div class="card-hotel__rating_mob" style=" display: flex; flex-direction: row; gap: 6px; align-items: center; ">
						<div class="value" style="border-radius: 3px; background: #024849; padding: 0 6px; color: #FFF; text-align: center; font-size: 12px; font-weight: 700; display: flex; align-items: center; height: 20px; ">${card.rating_stat}</div>
						<span class="text" style="color: #828282; text-align: center; font-family: Manrope; font-size: 12px; font-style: normal; font-weight: 400; line-height: normal; ">${card.rating_stat_text}</span>
					</div>
					<div class="hotel-top__location">
						<svg width="14" height="16" viewBox="0 0 14 16" style="width: 14px; height: 16px; flex-shrink: 0;" fill="none" xmlns="http://www.w3.org/2000/svg">
							<path d="M2.05034 2.04192C3.36309 0.734441 5.14355 -9.15527e-05 7.00005 -9.15527e-05C8.85655 -9.15527e-05 10.637 0.734441 11.9498 2.04192C13.2625 3.34939 14 5.12271 14 6.97176C14 8.82081 13.2625 10.5941 11.9498 11.9016L10.9955 12.8416C10.2921 13.5286 9.37964 14.4126 8.25738 15.4935C7.92007 15.8183 7.46924 15.9999 7.00005 15.9999C6.53086 15.9999 6.08003 15.8183 5.74273 15.4935L2.93626 12.7744C2.58334 12.4293 2.2883 12.1386 2.05034 11.9016C1.40031 11.2542 0.884667 10.4857 0.532868 9.63979C0.181069 8.79393 0 7.88733 0 6.97176C0 6.0562 0.181069 5.1496 0.532868 4.30373C0.884667 3.45786 1.40031 2.6893 2.05034 2.04192ZM11.0968 2.89065C10.0101 1.80848 8.53622 1.20061 6.99948 1.20076C5.46275 1.20091 3.98902 1.80907 2.90249 2.89145C1.81596 3.97383 1.20565 5.44176 1.2058 6.97233C1.20595 8.50289 1.81656 9.97071 2.9033 11.0529L4.09792 12.2283C4.92312 13.0313 5.75062 13.832 6.58041 14.6304C6.69285 14.7387 6.84319 14.7993 6.99965 14.7993C7.15611 14.7993 7.30644 14.7387 7.41889 14.6304L10.1474 11.9881C10.5252 11.619 10.8412 11.3075 11.096 11.0529C12.1825 9.97069 12.7929 8.50296 12.7929 6.97256C12.7929 5.44216 12.1825 3.97443 11.096 2.89225L11.0968 2.89065ZM7.00005 4.78908C7.31698 4.78908 7.6308 4.85125 7.9236 4.97205C8.2164 5.09285 8.48245 5.2699 8.70655 5.4931C8.93065 5.7163 9.10842 5.98128 9.2297 6.27291C9.35098 6.56453 9.41341 6.8771 9.41341 7.19275C9.41341 7.50841 9.35098 7.82097 9.2297 8.1126C9.10842 8.40422 8.93065 8.6692 8.70655 8.8924C8.48245 9.1156 8.2164 9.29266 7.9236 9.41345C7.6308 9.53425 7.31698 9.59642 7.00005 9.59642C6.36772 9.58492 5.76519 9.32667 5.32209 8.87722C4.879 8.42777 4.63074 7.82305 4.63074 7.19315C4.63074 6.56326 4.879 5.95853 5.32209 5.50908C5.76519 5.05963 6.36772 4.80138 7.00005 4.78988V4.78908ZM7.00005 5.99012C6.84148 5.99012 6.68447 6.02122 6.53797 6.08166C6.39147 6.1421 6.25836 6.23068 6.14623 6.34236C6.03411 6.45403 5.94517 6.58661 5.88448 6.73252C5.8238 6.87843 5.79257 7.03482 5.79257 7.19275C5.79257 7.35068 5.8238 7.50707 5.88448 7.65298C5.94517 7.79889 6.03411 7.93147 6.14623 8.04314C6.25836 8.15482 6.39147 8.2434 6.53797 8.30384C6.68447 8.36428 6.84148 8.39539 7.00005 8.39539C7.32019 8.39539 7.62721 8.26872 7.85359 8.04326C8.07996 7.8178 8.20713 7.512 8.20713 7.19315C8.20713 6.8743 8.07996 6.56851 7.85359 6.34304C7.62721 6.11758 7.32019 5.99092 7.00005 5.99092V5.99012Z" fill="#FC7201"></path>
							<path d="M2.05034 2.04192C3.36309 0.734441 5.14355 -9.15527e-05 7.00005 -9.15527e-05C8.85655 -9.15527e-05 10.637 0.734441 11.9498 2.04192C13.2625 3.34939 14 5.12271 14 6.97176C14 8.82081 13.2625 10.5941 11.9498 11.9016L10.9955 12.8416C10.2921 13.5286 9.37964 14.4126 8.25738 15.4935C7.92007 15.8183 7.46924 15.9999 7.00005 15.9999C6.53086 15.9999 6.08003 15.8183 5.74273 15.4935L2.93626 12.7744C2.58334 12.4293 2.2883 12.1386 2.05034 11.9016C1.40031 11.2542 0.884667 10.4857 0.532868 9.63979C0.181069 8.79393 0 7.88733 0 6.97176C0 6.0562 0.181069 5.1496 0.532868 4.30373C0.884667 3.45786 1.40031 2.6893 2.05034 2.04192ZM11.0968 2.89065C10.0101 1.80848 8.53622 1.20061 6.99948 1.20076C5.46275 1.20091 3.98902 1.80907 2.90249 2.89145C1.81596 3.97383 1.20565 5.44176 1.2058 6.97233C1.20595 8.50289 1.81656 9.97071 2.9033 11.0529L4.09792 12.2283C4.92312 13.0313 5.75062 13.832 6.58041 14.6304C6.69285 14.7387 6.84319 14.7993 6.99965 14.7993C7.15611 14.7993 7.30644 14.7387 7.41889 14.6304L10.1474 11.9881C10.5252 11.619 10.8412 11.3075 11.096 11.0529C12.1825 9.97069 12.7929 8.50296 12.7929 6.97256C12.7929 5.44216 12.1825 3.97443 11.096 2.89225L11.0968 2.89065ZM7.00005 4.78908C7.31698 4.78908 7.6308 4.85125 7.9236 4.97205C8.2164 5.09285 8.48245 5.2699 8.70655 5.4931C8.93065 5.7163 9.10842 5.98128 9.2297 6.27291C9.35098 6.56453 9.41341 6.8771 9.41341 7.19275C9.41341 7.50841 9.35098 7.82097 9.2297 8.1126C9.10842 8.40422 8.93065 8.6692 8.70655 8.8924C8.48245 9.1156 8.2164 9.29266 7.9236 9.41345C7.6308 9.53425 7.31698 9.59642 7.00005 9.59642C6.36772 9.58492 5.76519 9.32667 5.32209 8.87722C4.879 8.42777 4.63074 7.82305 4.63074 7.19315C4.63074 6.56326 4.879 5.95853 5.32209 5.50908C5.76519 5.05963 6.36772 4.80138 7.00005 4.78988V4.78908ZM7.00005 5.99012C6.84148 5.99012 6.68447 6.02122 6.53797 6.08166C6.39147 6.1421 6.25836 6.23068 6.14623 6.34236C6.03411 6.45403 5.94517 6.58661 5.88448 6.73252C5.8238 6.87843 5.79257 7.03482 5.79257 7.19275C5.79257 7.35068 5.8238 7.50707 5.88448 7.65298C5.94517 7.79889 6.03411 7.93147 6.14623 8.04314C6.25836 8.15482 6.39147 8.2434 6.53797 8.30384C6.68447 8.36428 6.84148 8.39539 7.00005 8.39539C7.32019 8.39539 7.62721 8.26872 7.85359 8.04326C8.07996 7.8178 8.20713 7.512 8.20713 7.19315C8.20713 6.8743 8.07996 6.56851 7.85359 6.34304C7.62721 6.11758 7.32019 5.99092 7.00005 5.99092V5.99012Z" fill="black" fill-opacity="0.2"></path>
						</svg>
						<p class="hotel-top__text" style="color: #FC7A11; font-family: Manrope; font-size: 13px; font-style: normal; font-weight: 400; line-height: normal;">${card.address}</p>
					</div>
					${apartment_text_html}
				</div>

				<div class="hotel-top__left" style="width: 266px;text-align: end;display: flex;margin-left: auto;">
						<span class="text" style="margin: -6px 0;">${text_under_price}</span>
						<button class="hotel-top__button" style="width: 190px;">
							<a target="_blank"
								href="/hotel/${card.id}/${queryString}"
								style="color:inherit">${card.min_price} ₽</a>
						</button>
					</div>
				</div>
			</div>
		</li>
		`)
	}
	else {
		// --- Телефон --- //

		let hotel_top__stars_html = "";
		if (card.stars_text.length > 0) {
			hotel_top__stars_html = `<div class="hotel-top__stars" style="font-size: 27px; height: 36px; margin-top: -14px; color: #FC7201;">${card.stars_text}</div>`
		}

		if (card.apartment_text) {
			apartment_text_html = `
				<span style="color: #828282; font-family: Manrope; font-size: 14px; font-style: normal; font-weight: 400; line-height: 123.6%; display: block;">${card.apartment_text}</span>
			`
		}
		else {
			apartment_text_html = ""
		}


		var elem = $(`
		<li class="card-hotel__item" data-card-type=${type}>
		<div class="card-hotel__img">
			<div class="card_hotel_img_grupe" style="width: 100%; height: 100%;"></div>
			<div class="favorite_icon full c_point off" style="height: 26px; width: 26px;" data-hotel-id=${card.id}>
				<img width="19" height="19" src="/static/img/favorite_icon_off.png" class="off" alt="">
				<img width="19" height="19" src="/static/img/favorite_icon_on.png" class="on" alt="">
			</div>
		</div>
		<div class="card-hotel__body" style="padding: 7px;">
			<div class="hotel-top" style="display: flex; flex-direction: column; justify-content: space-between; height: 100%; width: 100%;">
				<div class="hotel-top__right" style="margin-bottom: 10px; display: flex; flex-direction: column; gap: 6px;">
					<a target="_blank"
						href="/hotel/${card.id}/${queryString}"
						class="hotel-top__title" style="margin-bottom: 0">${card.name}</a>

					${hotel_top__stars_html}
					<div class="card-hotel__rating_mob" style=" display: flex; flex-direction: row; gap: 6px; align-items: center; ">
						<div class="value" style="border-radius: 3px; background: #024849; padding: 0 6px; color: #FFF; text-align: center; font-size: 12px; font-weight: 700; display: flex; align-items: center; height: 20px; ">${card.rating_stat}</div>
						<span class="text" style="color: #828282; text-align: center; font-family: Manrope; font-size: 12px; font-style: normal; font-weight: 400; line-height: normal; ">${card.rating_stat_text}</span>
					</div>
					<div class="hotel-top__location">
						<svg width="14" height="16" viewBox="0 0 14 16" style="width: 14px; height: 16px; flex-shrink: 0;" fill="none" xmlns="http://www.w3.org/2000/svg">
							<path d="M2.05034 2.04192C3.36309 0.734441 5.14355 -9.15527e-05 7.00005 -9.15527e-05C8.85655 -9.15527e-05 10.637 0.734441 11.9498 2.04192C13.2625 3.34939 14 5.12271 14 6.97176C14 8.82081 13.2625 10.5941 11.9498 11.9016L10.9955 12.8416C10.2921 13.5286 9.37964 14.4126 8.25738 15.4935C7.92007 15.8183 7.46924 15.9999 7.00005 15.9999C6.53086 15.9999 6.08003 15.8183 5.74273 15.4935L2.93626 12.7744C2.58334 12.4293 2.2883 12.1386 2.05034 11.9016C1.40031 11.2542 0.884667 10.4857 0.532868 9.63979C0.181069 8.79393 0 7.88733 0 6.97176C0 6.0562 0.181069 5.1496 0.532868 4.30373C0.884667 3.45786 1.40031 2.6893 2.05034 2.04192ZM11.0968 2.89065C10.0101 1.80848 8.53622 1.20061 6.99948 1.20076C5.46275 1.20091 3.98902 1.80907 2.90249 2.89145C1.81596 3.97383 1.20565 5.44176 1.2058 6.97233C1.20595 8.50289 1.81656 9.97071 2.9033 11.0529L4.09792 12.2283C4.92312 13.0313 5.75062 13.832 6.58041 14.6304C6.69285 14.7387 6.84319 14.7993 6.99965 14.7993C7.15611 14.7993 7.30644 14.7387 7.41889 14.6304L10.1474 11.9881C10.5252 11.619 10.8412 11.3075 11.096 11.0529C12.1825 9.97069 12.7929 8.50296 12.7929 6.97256C12.7929 5.44216 12.1825 3.97443 11.096 2.89225L11.0968 2.89065ZM7.00005 4.78908C7.31698 4.78908 7.6308 4.85125 7.9236 4.97205C8.2164 5.09285 8.48245 5.2699 8.70655 5.4931C8.93065 5.7163 9.10842 5.98128 9.2297 6.27291C9.35098 6.56453 9.41341 6.8771 9.41341 7.19275C9.41341 7.50841 9.35098 7.82097 9.2297 8.1126C9.10842 8.40422 8.93065 8.6692 8.70655 8.8924C8.48245 9.1156 8.2164 9.29266 7.9236 9.41345C7.6308 9.53425 7.31698 9.59642 7.00005 9.59642C6.36772 9.58492 5.76519 9.32667 5.32209 8.87722C4.879 8.42777 4.63074 7.82305 4.63074 7.19315C4.63074 6.56326 4.879 5.95853 5.32209 5.50908C5.76519 5.05963 6.36772 4.80138 7.00005 4.78988V4.78908ZM7.00005 5.99012C6.84148 5.99012 6.68447 6.02122 6.53797 6.08166C6.39147 6.1421 6.25836 6.23068 6.14623 6.34236C6.03411 6.45403 5.94517 6.58661 5.88448 6.73252C5.8238 6.87843 5.79257 7.03482 5.79257 7.19275C5.79257 7.35068 5.8238 7.50707 5.88448 7.65298C5.94517 7.79889 6.03411 7.93147 6.14623 8.04314C6.25836 8.15482 6.39147 8.2434 6.53797 8.30384C6.68447 8.36428 6.84148 8.39539 7.00005 8.39539C7.32019 8.39539 7.62721 8.26872 7.85359 8.04326C8.07996 7.8178 8.20713 7.512 8.20713 7.19315C8.20713 6.8743 8.07996 6.56851 7.85359 6.34304C7.62721 6.11758 7.32019 5.99092 7.00005 5.99092V5.99012Z" fill="#FC7201"></path>
							<path d="M2.05034 2.04192C3.36309 0.734441 5.14355 -9.15527e-05 7.00005 -9.15527e-05C8.85655 -9.15527e-05 10.637 0.734441 11.9498 2.04192C13.2625 3.34939 14 5.12271 14 6.97176C14 8.82081 13.2625 10.5941 11.9498 11.9016L10.9955 12.8416C10.2921 13.5286 9.37964 14.4126 8.25738 15.4935C7.92007 15.8183 7.46924 15.9999 7.00005 15.9999C6.53086 15.9999 6.08003 15.8183 5.74273 15.4935L2.93626 12.7744C2.58334 12.4293 2.2883 12.1386 2.05034 11.9016C1.40031 11.2542 0.884667 10.4857 0.532868 9.63979C0.181069 8.79393 0 7.88733 0 6.97176C0 6.0562 0.181069 5.1496 0.532868 4.30373C0.884667 3.45786 1.40031 2.6893 2.05034 2.04192ZM11.0968 2.89065C10.0101 1.80848 8.53622 1.20061 6.99948 1.20076C5.46275 1.20091 3.98902 1.80907 2.90249 2.89145C1.81596 3.97383 1.20565 5.44176 1.2058 6.97233C1.20595 8.50289 1.81656 9.97071 2.9033 11.0529L4.09792 12.2283C4.92312 13.0313 5.75062 13.832 6.58041 14.6304C6.69285 14.7387 6.84319 14.7993 6.99965 14.7993C7.15611 14.7993 7.30644 14.7387 7.41889 14.6304L10.1474 11.9881C10.5252 11.619 10.8412 11.3075 11.096 11.0529C12.1825 9.97069 12.7929 8.50296 12.7929 6.97256C12.7929 5.44216 12.1825 3.97443 11.096 2.89225L11.0968 2.89065ZM7.00005 4.78908C7.31698 4.78908 7.6308 4.85125 7.9236 4.97205C8.2164 5.09285 8.48245 5.2699 8.70655 5.4931C8.93065 5.7163 9.10842 5.98128 9.2297 6.27291C9.35098 6.56453 9.41341 6.8771 9.41341 7.19275C9.41341 7.50841 9.35098 7.82097 9.2297 8.1126C9.10842 8.40422 8.93065 8.6692 8.70655 8.8924C8.48245 9.1156 8.2164 9.29266 7.9236 9.41345C7.6308 9.53425 7.31698 9.59642 7.00005 9.59642C6.36772 9.58492 5.76519 9.32667 5.32209 8.87722C4.879 8.42777 4.63074 7.82305 4.63074 7.19315C4.63074 6.56326 4.879 5.95853 5.32209 5.50908C5.76519 5.05963 6.36772 4.80138 7.00005 4.78988V4.78908ZM7.00005 5.99012C6.84148 5.99012 6.68447 6.02122 6.53797 6.08166C6.39147 6.1421 6.25836 6.23068 6.14623 6.34236C6.03411 6.45403 5.94517 6.58661 5.88448 6.73252C5.8238 6.87843 5.79257 7.03482 5.79257 7.19275C5.79257 7.35068 5.8238 7.50707 5.88448 7.65298C5.94517 7.79889 6.03411 7.93147 6.14623 8.04314C6.25836 8.15482 6.39147 8.2434 6.53797 8.30384C6.68447 8.36428 6.84148 8.39539 7.00005 8.39539C7.32019 8.39539 7.62721 8.26872 7.85359 8.04326C8.07996 7.8178 8.20713 7.512 8.20713 7.19315C8.20713 6.8743 8.07996 6.56851 7.85359 6.34304C7.62721 6.11758 7.32019 5.99092 7.00005 5.99092V5.99012Z" fill="black" fill-opacity="0.2"></path>
						</svg>
						<p class="hotel-top__text" style="color: #FC7A11; font-family: Manrope; font-size: 13px; font-style: normal; font-weight: 400; line-height: normal;">${card.address}</p>
					</div>
					${apartment_text_html}
				</div>

				<div class="hotel-top__left" style="width: 100%; text-align: end;">
						<span class="text" style="margin: 6px 0;">${text_under_price}</span>
						<button class="hotel-top__button" style="width: 100%;">
							<a target="_blank"
								href="/hotel/${card.id}/${queryString}"
								style="color:inherit">${card.min_price} ₽</a>
						</button>
					</div>
				</div>
			</div>
		</li>
		`)
	}


	card.imgs.forEach(function (img, index) {
		imgTag = $(`<img class="c_point" data-src="${img}" loading="lazy">`);
		if (index > 0) {
			imgTag.hide();
		}
		imgTag.click(function () {
			next = $(this).next("img")
			if ($(next).length) {
				$(this).hide()
				$(next).show()
			}
			else {
				$(elem).find(".card_hotel_img_grupe img").first().show()
				$(this).hide()
			}
		})
		$(elem).find(".card_hotel_img_grupe").append(imgTag);
	});

	return elem
}

full_card_grupe = false

function set_hotel_card(cards, hotel_count) {


	if (!full_card_grupe) {
		card_hotel_body.html("")
	}

	index_card = 0

	$(".card-hotel__item .card_hotel_img_grupe img").map(function () {
		src = $(this).attr("src")
		URL.revokeObjectURL(src);
	})

	cards.forEach(card => {

		let elem = gen_card_hotel_to_list(card)

		$(card_hotel_body).append(elem)

		index_card++;
	});

	get_favorite()

	if (cards.length == 0) {
		$(card_hotel_body).append("<div style='position: relative; display: flex; justify-content: center; font-size: 22px; text-align: center; text-decoration: none; color: #000000; cursor: pointer; height: 62px; align-items: center; background: #e3e3e3; border-radius: 15px;'>Ничего не найдено</div>")
	}

	if (hotel_count.cur > 20) {
		full_card_grupe = true
		$("#next_card-hotel").remove()
		$(card_hotel_body).append("<div style='position: relative; display: flex; justify-content: center; font-size: 22px; text-align: center; text-decoration: none; color: #000000; cursor: pointer; height: 62px; align-items: center; background: #e3e3e3; border-radius: 15px;' id='next_card-hotel'>Ещё</div>")
	}

	if ($(".card-hotel__item").length == final_max_hotel_count_cur) {
		$("#next_card-hotel").remove()
	}

	$("img[data-src]").map(function () {
		$(this).attr("src", $(this).data("src"))
	})

	$('#next_card-hotel').click(function () {
		count_card_max += 20
		card_hotel_body.append(`<div class="loader" id="next_card_hotel_loading">loading</div>`)
		$('#next_card-hotel').remove()
		get_hotel_fillter_ajax()
	});
}

$(document).ready(function () {
	get_hotel_fillter()
});
