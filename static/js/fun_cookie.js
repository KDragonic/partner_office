function setCookie(cname, cvalue, exhour) {
	var d = new Date();
	d.setTime(d.getTime() + (exhour * 60 * 60 * 1000));
	var expires = "expires=" + d.toUTCString();
	document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie(cname) {
	var name = cname + "=";
	var ca = document.cookie.split(';');
	for (var i = 0; i < ca.length; i++) {
		var c = ca[i];
		while (c.charAt(0) == ' ') {
			c = c.substring(1);
		}
		if (c.indexOf(name) == 0) {
			return c.substring(name.length, c.length);
		}
	}
	return "";
}

function checkCookie(cname) {
	var cookie = getCookie(cname);
	if (cookie != "" && cookie != null) {
		return true
	}
	return false
}


// Посторонние методы

function go_page_login(url=null) {
	if (url == null) {
		setCookie("back_url_login_page", location.href)
	}
	else {
		setCookie("back_url_login_page", url)
	}
	location.href = "/login/"
}

function set_url_back_url_login_page() {
	if (checkCookie("back_url_login_page")) {
			let url = getCookie("back_url_login_page")
			if (url != null) {
					location.href = url
					return true
			}
	}
	location.href = "/profile/"
	return false
}


open_reminders_popup = false

reminders_interval = null

function reset_reminders_interval() {
	// Проверка куки на наличие списка напоминаний
	if (checkCookie("reminders")) {

		if (reminders_interval) {
			clearInterval(reminders_interval)
		}

		// Проверка каждую минуту на наступление времени напоминания
		reminders_interval = setInterval(() => {
			const currentTime = new Date().getTime();

			reminders = JSON.parse(getCookie("reminders"));
			reminders.forEach((reminder, index, _) => {
				const timeRemaining = Math.round((reminder.time - currentTime) / 1000);
				console.log(`Напоминание: ${reminder.title} => ${timeRemaining} с`);
				if (currentTime >= reminder.time) {
					if (!open_reminders_popup) {
						popup_create("Напоминание", reminder.title,  [], [])
						open_reminders_popup = true
					}

					console.log("Напоминания достигнуто")

					setTimeout(() => {
						reminders.splice(index, 1)
						console.log("Напоминания удалёно")
						setCookie("reminders", JSON.stringify(reminders), 1);
					}, 10000);
				}
			});
		}, 2);
	}
}


reset_reminders_interval()


function removeAllReminder() {
	setCookie("reminders", JSON.stringify([]), 999);
}

function addReminder(title, time) {

	if (!title) {
		title = "Напоминание"
	}

	if (new Date().getTime() >= time) {
		return
	}

	let reminders = []
	if (checkCookie("reminders")) {
		reminders = JSON.parse(getCookie("reminders"));
	}

  const reminder = {
    title: title,
    time: time,
  };

  reminders.push(reminder);
  setCookie("reminders", JSON.stringify(reminders), 999);
	reset_reminders_interval()
}