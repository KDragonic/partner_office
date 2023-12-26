// Скролл цены

label_price = $(".price__title")
$(label_price).html("Цена: от - до");
price_value = [ 500, 300000 ]

elem_price = $(".filter-select__row--range__price")[0]

input_grupe_price = $(".filter-select__row--range__price_input_grupe")

noUiSlider.create(elem_price, {
	start: [500, 300000],
	step: 100,
	connect: true,
	range: {
		'min': 500,
		'max': 300000
	}
});

price_input_min = $(input_grupe_price).find("[name='price_input_min']")
price_input_max = $(input_grupe_price).find("[name='price_input_max']")

$(price_input_min).attr({"max": 300000, "min": 500})
$(price_input_max).attr({"max": 300000, "min": 500})

$(price_input_min).val(500)
$(price_input_max).val(300000)

$(price_input_min).change(function (){
	val = $(this).val()
	elem_price.noUiSlider.set([val, null])
	price_value = elem_price.noUiSlider.get(true)
	get_hotel_fillter()
})

$(price_input_max).change(function (){
	val = $(this).val()
	elem_price.noUiSlider.set([null, val])
	price_value = elem_price.noUiSlider.get(true)
	get_hotel_fillter()
})

elem_price.noUiSlider.on('update', function (values, handle) {
	$(price_input_min).val(parseInt(values[0]))
	$(price_input_max).val(parseInt(values[1]))
});

elem_price.noUiSlider.on('end', function (values, handle) {
	price_value = values
	get_hotel_fillter()
});




// Скролл растояния

label_duration = $(".duration__title")
$(label_duration).html("Расстояние от центра: 100 км 0 м");
duration_value = 100000
elem_duration = $(".filter-select__row--range__duration")[0]


noUiSlider.create(elem_duration, {
	start: 100,
	step: 1,
	connect: true,
	range: {
		'min': 0,
		'max': 100,
	}
});

input_grupe_duration = $(".filter-select__row--range__duration_input_grupe")
duration_input_max = $(input_grupe_duration).find("[name='duration_input_max']")

$(duration_input_max).attr({"max": 100})

$(duration_input_max).val(100)


$(duration_input_max).change(function (){
	val = $(this).val()
	elem_duration.noUiSlider.set(val)
	duration_value = elem_duration.noUiSlider.get(true) * 1000
	get_hotel_fillter()
})

elem_duration.noUiSlider.on('update', function (value, handle) {
	$(duration_input_max).val(parseInt(value))
});

elem_duration.noUiSlider.on('end', function (value, handle) {
	duration_value = value * 1000
	get_hotel_fillter()
});