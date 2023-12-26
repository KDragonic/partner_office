function add_hotel_item_to_parser_list() {
	$.ajax({
		method: 'POST',
		data: {
			"link": $(".search_bar_input").text()
		},
		url: "/admin/parser/api/hotel/add/",
		beforeSend: function (request) {
			request.setRequestHeader('X-CSRFToken', getCookie('csrftoken'))
		},
		success: function (request) {
			if (request?.popup) {
				popup_create(request.popup.title, request.popup.text, [], [], request.popup.type)
			}
		}
	})
}

cards_data = {}

function ajax_hotel_list_get() {
	$.ajax({
		method: 'GET',
		url: "/admin/parser/api/hotel/get/",
		success: function (request) {
			cards_data = {}
			$("#cards").empty()
			request.list.forEach((item, index) => {
				cards_data[index] = item

				let name = item.hasOwnProperty('name') ? item.name : "ID:" + item.id;
				let el;
				if (item.hasOwnProperty('img')) {
					img_src = item.img
					el = $(`
					<div class='card' type-status="${item['status']}" data-index=${index}>
						<img src="${img_src}">
						<div class="card_body">
							<span class="name">${name}</span>
							<span class="status" color-type="${item['status']}">${item['status_text']}</span>
						</div>
					</div>
					`)
				}
				else {
					el = $(`
					<div class='card' type-status="${item['status']}" data-index=${index}>
						<div class="card_body">
							<span class="name">${name}</span>
							<span class="status" color-type="${item['status']}">${item['status_text']}</span>
						</div>
					</div>
					`)
				}


				$("#cards").append(el);

			});
		}
	})
}

transfer_to_website = {
	"active": false,
	"user": {
		"username": "",
		"lastname": "",
		"middlename": "",
		"email": "",
		"phone": "",
		"login": "",
		"password": "",
	},
	"hotels": {}
}

$(".cards_section").on("click", ".form_of_materialization.show .title", function () {
	$(".form_of_materialization").addClass("hide")
	$(".form_of_materialization").removeClass("show")
	transfer_to_website["active"] = false
	$(`#cards .card`).not(`[type-status="download"]`).show().animate({ left: "-100%" }, 0, function () { $(this).animate({ left: "0" }, 500 )})
})

$(".cards_section").on("click", ".form_of_materialization.hide", function () {
	$(".form_of_materialization").removeClass("hide")
	$(".form_of_materialization").addClass("show")
	transfer_to_website["active"] = true
	$(`#cards .card`).not(`[type-status="download"]`).animate({ left: "0" }, 0, function () { $(this).animate({ left: "-100%" }, 500, function () { $(this).hide() }) })
})

$("#cards").on("click", ".card", function () {
	if (transfer_to_website["active"]) {
		$(this).toggleClass("selected")
		let index_obj = parseInt($(this).data("index"))

		if ($(this).hasClass("selected")) {
			let id = cards_data[index_obj]["id"]
			transfer_to_website["hotels"][index_obj] = id
		}
		else {
			let keys = Object.keys(transfer_to_website["hotels"]).map(Number);
			if (index_obj in keys || index_obj == [index_obj]) {
				delete transfer_to_website["hotels"][index_obj]
			}
		}

		transfer_to_website["hotels"] = Object.fromEntries(Object.entries(transfer_to_website["hotels"]).sort((a, b) => a[0].localeCompare(b[0])));

		$("#form_of_materialization_hotel_list").empty()
		for (const key in transfer_to_website["hotels"]) {
			let name = cards_data[key]["name"]
			let el = `<div class='item'>${name}</div>`
			$("#form_of_materialization_hotel_list").append(el)
		}
	}
	else {
		let index = parseInt($(this).data("index"))
		let date = cards_data[index]
		let json_str = JSON.stringify(date, null, 2);
		popup_create("Информация",
			`<pre style=" font-size: 13px; width: 100%; ">${json_str}</pre>`, [], [], "max")
	}
})

$("#button_materialize_a_hotel").click(function() {
	materialize_a_hotel();
})

function materialize_a_hotel() {
		if (form_type == "new_user") {
			transfer_to_website["user"]["username"] = $(`[name="user_fio_username"]`).val().trim()
			transfer_to_website["user"]["lastname"] = $(`[name="user_fio_lastname"]`).val().trim()
			transfer_to_website["user"]["middlename"] = $(`[name="user_fio_middlename"]`).val().trim()
			transfer_to_website["user"]["email"] = $(`[name="user_email"]`).val().trim()
			transfer_to_website["user"]["phone"] = $(`[name="user_phone"]`).val().trim()
			transfer_to_website["user"]["login"] = $(`[name="user_login"]`).val().trim()
			transfer_to_website["user"]["password"] = $(`[name="user_password"]`).val().trim()
		}

		if (form_type == "existing_user") {
			transfer_to_website["user"]["id"] = $(`[name="user_id"]`).val().trim()
			transfer_to_website["user"]["email"] = $(`[name="user_email_2"]`).val().trim()
		}

		transfer_to_website["form_type"] = form_type

		$.ajax({
			method: 'POST',
			data: JSON.stringify(transfer_to_website),
			contentType: "application/json",
			dataType: "json",
			url: "/admin/parser/api/hotel/materialize_a_hotel/",
			beforeSend: function (request) {
				request.setRequestHeader('X-CSRFToken', getCookie('csrftoken'))
			},
			success: function (request) {
				if (request?.popup) {
					popup_create(request.popup.title, request.popup.text, [], [], request.popup.type)
				}
			}
		})
}

let form_type = "new_user"

$(`[button-event="form.change.new_user"]`).click(function() {
	$(this).addClass("active")
	$(`[button-event="form.change.existing_user"]`).removeClass("active")
	$(".form#existing_user").addClass("d-none")
	$(".form#new_user").removeClass("d-none")
	form_type = "new_user"
})

$(`[button-event="form.change.existing_user"]`).click(function() {
	$(this).addClass("active")
	$(`[button-event="form.change.new_user"]`).removeClass("active")
	$(".form#new_user").addClass("d-none")
	$(".form#existing_user").removeClass("d-none")
	form_type = "existing_user"
})



ajax_hotel_list_get()