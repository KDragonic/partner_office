$(document).ready(function () {
  var methods = {
    init: function (params) {
      var defaults = {
        "type": "login",
        "tab": "normal",
        "id": 0,
        "events": {},
        "forms": {
          "login": {
            "label": "Вход",
            "tabs": {
              "sms_1": {
                "show": true,
                "label": "Телефон",
                "css": {
                  "style": {
                    "default": {
                      "background": "transparent",
                      "transition": "all 0.05s"
                    },
                    "hover": {
                      "background": "#A3DFA2"
                    },
                    "click": {
                      "background": "#87E785"
                    },
                    "class": {
                      "active": {
                        "background": "#86C685"
                      }
                    }
                  }
                },
                "сontrols": [
                  {
                    "type": "text",
                    "options": {
                      "label": "Вход",
                      "css": {
                        "style": {
                          "default": {
                            "color": "#000",
                            "font-size": "32px",
                            "text-align": "center",
                            "margin-bottom": "12px"
                          }
                        }
                      }
                    }
                  },
                  {
                    "type": "input",
                    "options": {
                      "code": "phone",
                      "label": "Номер телефона",
                      "type": "text",
                      "placeholder": [
                        "+79261234567",
                        "+7 (985) 678-90-12",
                        "+7 499 876-54-32",
                        "89112345678"
                      ]
                    }
                  },
                  {
                    "type": "text",
                    "options": {
                      "label": "Введите ваш номер телефона. После нажатия на кнопку вам поступит звонок. <b>Отвечать на звонок не нужно.</b>  ",
                      "css": {
                        "style": {
                          "default": {
                            "color": "#333333",
                            "font-size": "14px",
                            "text-align": "center",
                            "margin-bottom": "10px"
                          }
                        }
                      }
                    }
                  },
                  {
                    "type": "button",
                    "options": {
                      "label": "Отправить",
                      "css": {
                        "style": {
                          "default": {
                            "background": "#86C685",
                            "color": "white",
                            "font-size": "32px",
                            "margin-bottom": "8px"
                          },
                          "hover": {
                            "background": "#66BB65"
                          },
                          "click": {
                            "background": "#AED4AE"
                          }
                        }
                      }
                    },
                    "events": {
                      "click": {
                        "type": "valid",
                        "options": {
                          "values": [
                            {
                              "code": "phone",
                              "valids": {
                                "len": {
                                  "min": 5,
                                  "max": 20
                                }
                              }
                            }
                          ],
                          "success": {
                            "type": "ajax",
                            "options": {
                              "method": "POST",
                              "url": "/api/upform/auth/phone/create_code/",
                              "values": {
                                "phone": {
                                  "code": "phone"
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  },
                  {
                    "type": "text",
                    "options": {
                      "label": "Регистрация",
                      "css": {
                        "style": {
                          "default": {
                            "color": "#333333",
                            "font-size": "16px",
                            "text-align": "center",
                            "cursor": "pointer",
                            "text-decoration": "underline",
                            "margin-top": "12px"
                          },
                          "hover": {
                            "color": "#4870BF"
                          },
                          "click": {
                            "color": "#4081FF"
                          }
                        }
                      }
                    },
                    "events": {
                      "click": {
                        "type": "form.change",
                        "options": {
                          "type": "reg",
                          "tab": "sms_1"
                        }
                      }
                    }
                  }
                ]
              },
              "sms_2": {
                "show": false,
                "label": "Телефон",
                "css": {
                  "style": {
                    "default": {
                      "background": "transparent",
                      "transition": "all 0.05s"
                    },
                    "hover": {
                      "background": "#A3DFA2"
                    },
                    "click": {
                      "background": "#87E785"
                    },
                    "class": {
                      "active": {
                        "background": "#86C685"
                      }
                    }
                  }
                },
                "сontrols": [
                  {
                    "type": "text",
                    "options": {
                      "label": "Вход",
                      "css": {
                        "style": {
                          "default": {
                            "color": "#000",
                            "font-size": "32px",
                            "text-align": "center",
                            "margin-bottom": "12px"
                          }
                        }
                      }
                    }
                  },
                  {
                    "type": "input",
                    "options": {
                      "code": "phone_code",
                      "label": "Код",
                      "type": "text",
                      "placeholder": [
                        "2564",
                        "3474",
                        "4674",
                        "4785"
                      ]
                    }
                  },
                  {
                    "type": "text",
                    "options": {
                      "label": "Последние 4 цифры номера",
                      "css": {
                        "style": {
                          "default": {
                            "color": "#333333",
                            "font-size": "14px",
                            "text-align": "center",
                            "margin-bottom": "10px"
                          }
                        }
                      }
                    }
                  },
                  {
                    "type": "button",
                    "options": {
                      "label": "Отправить",
                      "css": {
                        "style": {
                          "default": {
                            "background": "#86C685",
                            "color": "white",
                            "font-size": "32px",
                            "margin-bottom": "8px"
                          },
                          "hover": {
                            "background": "#66BB65"
                          },
                          "click": {
                            "background": "#AED4AE"
                          }
                        }
                      }
                    },
                    "events": {
                      "click": {
                        "type": "valid",
                        "options": {
                          "values": [
                            {
                              "code": "phone_code",
                              "valids": {
                                "len": {
                                  "min": 4,
                                  "max": 4
                                }
                              }
                            }
                          ],
                          "success": {
                            "type": "ajax",
                            "options": {
                              "method": "POST",
                              "url": "/api/upform/auth/phone/check_code/",
                              "values": {
                                "phone_code": {
                                  "code": "phone_code"
                                },
                                "phone": {
                                  "code": "phone"
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  },
                  {
                    "type": "text",
                    "options": {
                      "label": "Вход",
                      "css": {
                        "style": {
                          "default": {
                            "color": "#333333",
                            "font-size": "16px",
                            "text-align": "center",
                            "cursor": "pointer",
                            "text-decoration": "underline",
                            "margin-top": "12px"
                          },
                          "hover": {
                            "color": "#4870BF"
                          },
                          "click": {
                            "color": "#4081FF"
                          }
                        }
                      }
                    },
                    "events": {
                      "click": {
                        "type": "form.change",
                        "options": {
                          "type": "reg",
                          "tab": "sms_1"
                        }
                      }
                    }
                  }
                ]
              },
              "social": {
                "show": true,
                "label": "Соц. сети",
                "css": {
                  "style": {
                    "default": {
                      "background": "transparent",
                      "transition": "all 0.05s"
                    },
                    "hover": {
                      "background": "#A3DFA2"
                    },
                    "click": {
                      "background": "#87E785"
                    },
                    "class": {
                      "active": {
                        "background": "#86C685"
                      }
                    }
                  }
                },
                "сontrols": [
                  {
                    "type": "text",
                    "options": {
                      "label": "",
                      "css": {
                        "style": {
                          "default": {
                            "color": "#000",
                            "font-size": "32px",
                            "text-align": "center",
                            "margin-bottom": "12px"
                          }
                        }
                      }
                    }
                  },
                  {
                    "type": "html",
                    "options": {
                      "css": {
                        "style": {
                          "default": {
                            "color": "#4C75A3",
                            "font-size": "32px",
                            "margin": "0 auto",
                            "cursor": "pointer"
                          }
                        }
                      },
                      "html": "<div class=\"item\"><svg xmlns=\"http://www.w3.org/2000/svg\" width=\"54\" height=\"54\" viewBox=\"0 0 54 54\" fill=\"none\"><path d=\"M33.9142 4.5H20.1083C7.49925 4.5 4.5 7.49925 4.5 20.0858V33.8918C4.5 46.4985 7.47675 49.5 20.0858 49.5H33.8918C46.4985 49.5 49.5 46.5233 49.5 33.9142V20.1083C49.5 7.49925 46.5233 4.5 33.9142 4.5ZM40.8285 36.6075H37.5457C36.3038 36.6075 35.9303 35.6018 33.7028 33.3743C31.7588 31.5 30.9375 31.266 30.4447 31.266C29.7653 31.266 29.5785 31.4527 29.5785 32.391V35.343C29.5785 36.1418 29.3197 36.6097 27.234 36.6097C25.2098 36.4737 23.2468 35.8587 21.5068 34.8154C19.7669 33.7722 18.2996 32.3304 17.226 30.609C14.6771 27.4365 12.9036 23.713 12.0465 19.7347C12.0465 19.242 12.2333 18.7965 13.1715 18.7965H16.452C17.2957 18.7965 17.5995 19.1723 17.9303 20.0385C19.5232 24.7275 22.2412 28.8045 23.3438 28.8045C23.7668 28.8045 23.9513 28.6178 23.9513 27.5625V22.734C23.8118 20.5312 22.6418 20.3445 22.6418 19.548C22.6568 19.3379 22.7531 19.1419 22.9101 19.0017C23.0672 18.8614 23.2728 18.7878 23.4832 18.7965H28.6403C29.3445 18.7965 29.5785 19.1475 29.5785 19.9913V26.5072C29.5785 27.2115 29.8822 27.4455 30.0938 27.4455C30.5168 27.4455 30.843 27.2115 31.617 26.4375C33.2794 24.4101 34.6377 22.1514 35.649 19.7325C35.7524 19.4419 35.948 19.1932 36.2059 19.0242C36.4639 18.8552 36.7701 18.7752 37.0778 18.7965H40.3605C41.3438 18.7965 41.553 19.2893 41.3438 19.9913C40.1501 22.6652 38.6732 25.2035 36.9382 27.5625C36.585 28.1025 36.4432 28.3837 36.9382 29.016C37.2645 29.5087 38.4142 30.4695 39.1882 31.383C40.313 32.5049 41.2471 33.803 41.9535 35.226C42.2347 36.1395 41.7645 36.6075 40.8285 36.6075Z\" fill=\"#4C75A3\"/></svg><span>ВКонтакте</span></div>"
                    },
                    "events": {
                      "click": {
                        "type": "href",
                        "options": {
                          "url": "https://oauth.vk.com/authorize?client_id=51619666&display=page&redirect_uri=https%3A%2F%2Fturgorodok.ru%2Fvk%2Flogin%2F&response_type=token&v=5.131&revoke=1",
                          "target": "_parent"
                        }
                      }
                    }
                  },
                  {
                    "type": "html",
                    "options": {
                      "css": {
                        "style": {
                          "default": {
                            "color": "#CD201F",
                            "font-size": "32px",
                            "margin": "0 auto",
                            "cursor": "pointer"
                          }
                        }
                      },
                      "html": "<div class=\"item\">\n                        <svg xmlns=\"http://www.w3.org/2000/svg\" width=\"45\" height=\"45\" viewBox=\"0 0 45 45\" fill=\"none\"> <path fill-rule=\"evenodd\" clip-rule=\"evenodd\" d=\"M22.5 19.6875V26.4375H33.6656C33.2156 29.3344 30.2906 34.9313 22.5 34.9313C15.7781 34.9313 10.2938 29.3625 10.2938 22.5C10.2938 15.6375 15.7781 10.0687 22.5 10.0687C26.325 10.0687 28.8844 11.7 30.3469 13.1062L35.6906 7.95937C32.2594 4.75312 27.8156 2.8125 22.5 2.8125C11.6156 2.8125 2.8125 11.6156 2.8125 22.5C2.8125 33.3844 11.6156 42.1875 22.5 42.1875C33.8625 42.1875 41.4 34.2 41.4 22.95C41.4 21.6562 41.2594 20.6719 41.0906 19.6875H22.5Z\" fill=\"#CD201F\"/> </svg>\n                        <span>Google</span>\n                      </div>"
                    },
                    "events": {
                      "click": {
                        "type": "href",
                        "options": {
                          "url": "https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=603454700126-si62m4apquu3abh894ft24png51d49av.apps.googleusercontent.com&redirect_uri=https%3A%2F%2Fturgorodok.ru%2Fgoogle%2Fauth%2F&scope=openid+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.email&state=vusIbQGqhpPOiVpj8ztXBIPhPhjfCZ&include_granted_scopes=true&access_type=offline",
                          "target": "_parent"
                        }
                      }
                    }
                  },
                ]
              },
              "normal": {
                "show": true,
                "label": "Пароль",
                "css": {
                  "style": {
                    "default": {
                      "background": "transparent",
                      "transition": "all 0.05s"
                    },
                    "hover": {
                      "background": "#A3DFA2"
                    },
                    "click": {
                      "background": "#87E785"
                    },
                    "class": {
                      "active": {
                        "background": "#86C685"
                      }
                    }
                  }
                },
                "сontrols": [
                  {
                    "type": "text",
                    "options": {
                      "label": "Вход",
                      "css": {
                        "style": {
                          "default": {
                            "color": "#000",
                            "font-size": "32px",
                            "text-align": "center",
                            "margin-bottom": "12px"
                          }
                        }
                      }
                    }
                  },
                  {
                    "type": "input",
                    "options": {
                      "code": "login",
                      "label": "Логин (Почта, Телефон)",
                      "type": "text",
                      "placeholder": [
                        "johndoe@gmail.com",
                        "sarahsmith@yahoo.com",
                        "michaeldavis@outlook.com",
                        "emilyjones@mail.ru",
                        "alexwilson@yandex.ru"
                      ]
                    }
                  },
                  {
                    "type": "input",
                    "options": {
                      "code": "password",
                      "label": "Пароль",
                      "type": "password",
                      "placeholder": "••••••••"
                    }
                  },
                  {
                    "type": "text",
                    "options": {
                      "label": "Забыл пароль",
                      "css": {
                        "style": {
                          "default": {
                            "color": "#333333",
                            "font-size": "16px",
                            "text-decoration-line": "underline",
                            "margin-bottom": "8px",
                            "cursor": "pointer"
                          },
                          "hover": {
                            "color": "#4870BF"
                          },
                          "click": {
                            "color": "#4081FF"
                          }
                        }
                      },
                    },
                    "events": {
                      "click": {
                        "type": "form.change",
                        "options": {
                          "type": "forget_password",
                          "tab": "stage_1"
                        }
                      }
                    }
                  },
                  {
                    "type": "button",
                    "options": {
                      "label": "Вход",
                      "css": {
                        "style": {
                          "default": {
                            "background": "#86C685",
                            "color": "white",
                            "font-size": "32px",
                            "margin-bottom": "8px"
                          },
                          "hover": {
                            "background": "#66BB65"
                          },
                          "click": {
                            "background": "#AED4AE"
                          }
                        }
                      },
                    },
                    "events": {
                      "click": {
                        "type": "valid",
                        "options": {
                          "values": [
                            {
                              "code": "login",
                              "valids": {
                                "len": {
                                  "min": 1,
                                  "max": 50
                                }
                              }
                            },
                            {
                              "code": "password",
                              "valids": {
                                "len": {
                                  "min": 1,
                                  "max": 50
                                }
                              }
                            }
                          ],
                          "success": {
                            "type": "ajax",
                            "options": {
                              "method": "POST",
                              "url": "/api/upform/auth/normal/login/",
                              "values": {
                                "login": {
                                  "code": "login"
                                },
                                "password": {
                                  "code": "password"
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  },
                  {
                    "type": "text",
                    "options": {
                      "label": "Регистрация",
                      "css": {
                        "style": {
                          "default": {
                            "color": "#333333",
                            "font-size": "16px",
                            "text-align": "center",
                            "cursor": "pointer",
                            "text-decoration": "underline",
                            "margin-top": "12px"
                          },
                          "hover": {
                            "color": "#4870BF"
                          },
                          "click": {
                            "color": "#4081FF"
                          }
                        }
                      }
                    },
                    "events": {
                      "click": {
                        "type": "form.change",
                        "options": {
                          "type": "reg",
                          "tab": ""
                        }
                      }
                    }
                  }
                ]
              }
            }
          },
          "reg": {
            "label": "Регистрация",
            "tabs": {
              "sms_1": {
                "show": true,
                "label": "Телефон",
                "css": {
                  "style": {
                    "default": {
                      "background": "transparent",
                      "transition": "all 0.05s"
                    },
                    "hover": {
                      "background": "#A3DFA2"
                    },
                    "click": {
                      "background": "#87E785"
                    },
                    "class": {
                      "active": {
                        "background": "#86C685"
                      }
                    }
                  }
                },
                "сontrols": [
                  {
                    "type": "text",
                    "options": {
                      "label": "Регистрация",
                      "css": {
                        "style": {
                          "default": {
                            "color": "#000",
                            "font-size": "32px",
                            "text-align": "center",
                            "margin-bottom": "12px"
                          }
                        }
                      }
                    }
                  },
                  {
                    "type": "input",
                    "options": {
                      "code": "phone",
                      "label": "Номер телефона",
                      "type": "text",
                      "placeholder": [
                        "+79261234567",
                        "+7 (985) 678-90-12",
                        "+7 499 876-54-32",
                        "89112345678"
                      ]
                    }
                  },
                  {
                    "type": "text",
                    "options": {
                      "label": "Введите ваш номер телефона. После нажатия на кнопку вам поступит звонок. <b>Отвечать на звонок не нужно.</b>  ",
                      "css": {
                        "style": {
                          "default": {
                            "color": "#333333",
                            "font-size": "14px",
                            "text-align": "center",
                            "margin-bottom": "10px"
                          }
                        }
                      }
                    }
                  },
                  {
                    "type": "button",
                    "options": {
                      "label": "Отправить",
                      "css": {
                        "style": {
                          "default": {
                            "background": "#86C685",
                            "color": "white",
                            "font-size": "32px",
                            "margin-bottom": "8px"
                          },
                          "hover": {
                            "background": "#66BB65"
                          },
                          "click": {
                            "background": "#AED4AE"
                          }
                        }
                      }
                    },
                    "events": {
                      "click": {
                        "type": "valid",
                        "options": {
                          "values": [
                            {
                              "code": "phone",
                              "valids": {
                                "len": {
                                  "min": 5,
                                  "max": 20
                                }
                              }
                            }
                          ],
                          "success": {
                            "type": "ajax",
                            "options": {
                              "method": "POST",
                              "url": "/api/upform/auth/phone/create_code/",
                              "values": {
                                "phone": {
                                  "code": "phone"
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  },
                  {
                    "type": "text",
                    "options": {
                      "label": "Регистрация",
                      "css": {
                        "style": {
                          "default": {
                            "color": "#333333",
                            "font-size": "16px",
                            "text-align": "center",
                            "cursor": "pointer",
                            "text-decoration": "underline",
                            "margin-top": "12px"
                          },
                          "hover": {
                            "color": "#4870BF"
                          },
                          "click": {
                            "color": "#4081FF"
                          }
                        }
                      }
                    },
                    "events": {
                      "click": {
                        "type": "form.change",
                        "options": {
                          "type": "login",
                          "tab": "sms_1"
                        }
                      }
                    }
                  }
                ]
              },
              "sms_2": {
                "show": false,
                "label": "Телефон",
                "css": {
                  "style": {
                    "default": {
                      "background": "transparent",
                      "transition": "all 0.05s"
                    },
                    "hover": {
                      "background": "#A3DFA2"
                    },
                    "click": {
                      "background": "#87E785"
                    },
                    "class": {
                      "active": {
                        "background": "#86C685"
                      }
                    }
                  }
                },
                "сontrols": [
                  {
                    "type": "text",
                    "options": {
                      "label": "Регистрация",
                      "css": {
                        "style": {
                          "default": {
                            "color": "#000",
                            "font-size": "32px",
                            "text-align": "center",
                            "margin-bottom": "12px"
                          }
                        }
                      }
                    }
                  },
                  {
                    "type": "input",
                    "options": {
                      "code": "phone_code",
                      "label": "Код",
                      "type": "text",
                      "placeholder": [
                        "2564",
                        "3474",
                        "4674",
                        "4785"
                      ]
                    }
                  },
                  {
                    "type": "text",
                    "options": {
                      "label": "Последние 4 цифры номера",
                      "css": {
                        "style": {
                          "default": {
                            "color": "#333333",
                            "font-size": "14px",
                            "text-align": "center",
                            "margin-bottom": "10px"
                          }
                        }
                      }
                    }
                  },
                  {
                    "type": "button",
                    "options": {
                      "label": "Отправить",
                      "css": {
                        "style": {
                          "default": {
                            "background": "#86C685",
                            "color": "white",
                            "font-size": "32px",
                            "margin-bottom": "8px"
                          },
                          "hover": {
                            "background": "#66BB65"
                          },
                          "click": {
                            "background": "#AED4AE"
                          }
                        }
                      }
                    },
                    "events": {
                      "click": {
                        "type": "valid",
                        "options": {
                          "values": [
                            {
                              "code": "phone_code",
                              "valids": {
                                "len": {
                                  "min": 4,
                                  "max": 4
                                }
                              }
                            }
                          ],
                          "success": {
                            "type": "ajax",
                            "options": {
                              "method": "POST",
                              "url": "/api/upform/auth/phone/check_code/",
                              "values": {
                                "phone_code": {
                                  "code": "phone_code"
                                },
                                "phone": {
                                  "code": "phone"
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  },
                  {
                    "type": "text",
                    "options": {
                      "label": "Регистрация",
                      "css": {
                        "style": {
                          "default": {
                            "color": "#333333",
                            "font-size": "16px",
                            "text-align": "center",
                            "cursor": "pointer",
                            "text-decoration": "underline",
                            "margin-top": "12px"
                          },
                          "hover": {
                            "color": "#4870BF"
                          },
                          "click": {
                            "color": "#4081FF"
                          }
                        }
                      }
                    },
                    "events": {
                      "click": {
                        "type": "form.change",
                        "options": {
                          "type": "login",
                          "tab": "sms_1"
                        }
                      }
                    }
                  }
                ]
              },
              "social": {
                "show": true,
                "label": "Соц. сети",
                "css": {
                  "style": {
                    "default": {
                      "background": "transparent",
                      "transition": "all 0.05s"
                    },
                    "hover": {
                      "background": "#A3DFA2"
                    },
                    "click": {
                      "background": "#87E785"
                    },
                    "class": {
                      "active": {
                        "background": "#86C685"
                      }
                    }
                  }
                },
                "сontrols": [
                  {
                    "type": "text",
                    "options": {
                      "label": "",
                      "css": {
                        "style": {
                          "default": {
                            "color": "#000",
                            "font-size": "32px",
                            "text-align": "center",
                            "margin-bottom": "12px"
                          }
                        }
                      }
                    }
                  },
                  {
                    "type": "html",
                    "options": {
                      "css": {
                        "style": {
                          "default": {
                            "color": "#4C75A3",
                            "font-size": "32px",
                            "margin": "0 auto",
                            "cursor": "pointer"
                          }
                        }
                      },
                      "html": "<div class=\"item\">\n                        <svg xmlns=\"http://www.w3.org/2000/svg\" width=\"54\" height=\"54\" viewBox=\"0 0 54 54\" fill=\"none\"><path d=\"M33.9142 4.5H20.1083C7.49925 4.5 4.5 7.49925 4.5 20.0858V33.8918C4.5 46.4985 7.47675 49.5 20.0858 49.5H33.8918C46.4985 49.5 49.5 46.5233 49.5 33.9142V20.1083C49.5 7.49925 46.5233 4.5 33.9142 4.5ZM40.8285 36.6075H37.5457C36.3038 36.6075 35.9303 35.6018 33.7028 33.3743C31.7588 31.5 30.9375 31.266 30.4447 31.266C29.7653 31.266 29.5785 31.4527 29.5785 32.391V35.343C29.5785 36.1418 29.3197 36.6097 27.234 36.6097C25.2098 36.4737 23.2468 35.8587 21.5068 34.8154C19.7669 33.7722 18.2996 32.3304 17.226 30.609C14.6771 27.4365 12.9036 23.713 12.0465 19.7347C12.0465 19.242 12.2333 18.7965 13.1715 18.7965H16.452C17.2957 18.7965 17.5995 19.1723 17.9303 20.0385C19.5232 24.7275 22.2412 28.8045 23.3438 28.8045C23.7668 28.8045 23.9513 28.6178 23.9513 27.5625V22.734C23.8118 20.5312 22.6418 20.3445 22.6418 19.548C22.6568 19.3379 22.7531 19.1419 22.9101 19.0017C23.0672 18.8614 23.2728 18.7878 23.4832 18.7965H28.6403C29.3445 18.7965 29.5785 19.1475 29.5785 19.9913V26.5072C29.5785 27.2115 29.8822 27.4455 30.0938 27.4455C30.5168 27.4455 30.843 27.2115 31.617 26.4375C33.2794 24.4101 34.6377 22.1514 35.649 19.7325C35.7524 19.4419 35.948 19.1932 36.2059 19.0242C36.4639 18.8552 36.7701 18.7752 37.0778 18.7965H40.3605C41.3438 18.7965 41.553 19.2893 41.3438 19.9913C40.1501 22.6652 38.6732 25.2035 36.9382 27.5625C36.585 28.1025 36.4432 28.3837 36.9382 29.016C37.2645 29.5087 38.4142 30.4695 39.1882 31.383C40.313 32.5049 41.2471 33.803 41.9535 35.226C42.2347 36.1395 41.7645 36.6075 40.8285 36.6075Z\" fill=\"#4C75A3\"/></svg><span>ВКонтакте</span>\n                      </div>"
                    },
                    "events": {
                      "click": {
                        "type": "href",
                        "options": {
                          "url": "https://oauth.vk.com/authorize?client_id=51619666&display=page&redirect_uri=https%3A%2F%2Fturgorodok.ru%2Fvk%2Flogin%2F&response_type=token&v=5.131&revoke=1",
                          "target": "_parent"
                        }
                      }
                    }
                  },
                  {
                    "type": "html",
                    "options": {
                      "css": {
                        "style": {
                          "default": {
                            "color": "#CD201F",
                            "font-size": "32px",
                            "margin": "0 auto",
                            "cursor": "pointer"
                          }
                        }
                      },
                      "html": "<div class=\"item\">\n                        <svg xmlns=\"http://www.w3.org/2000/svg\" width=\"45\" height=\"45\" viewBox=\"0 0 45 45\" fill=\"none\"> <path fill-rule=\"evenodd\" clip-rule=\"evenodd\" d=\"M22.5 19.6875V26.4375H33.6656C33.2156 29.3344 30.2906 34.9313 22.5 34.9313C15.7781 34.9313 10.2938 29.3625 10.2938 22.5C10.2938 15.6375 15.7781 10.0687 22.5 10.0687C26.325 10.0687 28.8844 11.7 30.3469 13.1062L35.6906 7.95937C32.2594 4.75312 27.8156 2.8125 22.5 2.8125C11.6156 2.8125 2.8125 11.6156 2.8125 22.5C2.8125 33.3844 11.6156 42.1875 22.5 42.1875C33.8625 42.1875 41.4 34.2 41.4 22.95C41.4 21.6562 41.2594 20.6719 41.0906 19.6875H22.5Z\" fill=\"#CD201F\"/> </svg>\n                        <span>Google</span>\n                      </div>"
                    },
                    "events": {
                      "click": {
                        "type": "href",
                        "options": {
                          "url": "https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=603454700126-si62m4apquu3abh894ft24png51d49av.apps.googleusercontent.com&redirect_uri=https%3A%2F%2Fturgorodok.ru%2Fgoogle%2Fauth%2F&scope=openid+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.email&state=vusIbQGqhpPOiVpj8ztXBIPhPhjfCZ&include_granted_scopes=true&access_type=offline",
                          "target": "_parent"
                        }
                      }
                    }
                  },
                ]
              },
              "normal": {
                "show": true,
                "label": "Пароль",
                "css": {
                  "style": {
                    "default": {
                      "background": "transparent",
                      "transition": "all 0.05s"
                    },
                    "hover": {
                      "background": "#A3DFA2"
                    },
                    "click": {
                      "background": "#87E785"
                    },
                    "class": {
                      "active": {
                        "background": "#86C685"
                      }
                    }
                  }
                },
                "сontrols": [
                  {
                    "type": "text",
                    "options": {
                      "label": "Регистрация",
                      "css": {
                        "style": {
                          "default": {
                            "color": "#000",
                            "font-size": "32px",
                            "text-align": "center",
                            "margin-bottom": "12px"
                          }
                        }
                      }
                    }
                  },
                  {
                    "type": "input",
                    "options": {
                      "code": "fio",
                      "label": "ФИО",
                      "type": "text",
                      "placeholder": "\"ФИО\""
                    }
                  },
                  {
                    "type": "input",
                    "options": {
                      "code": "email",
                      "label": "Почта",
                      "type": "text",
                      "placeholder": [
                        "johndoe@gmail.com",
                        "sarahsmith@yahoo.com",
                        "michaeldavis@outlook.com",
                        "emilyjones@mail.ru",
                        "alexwilson@yandex.ru"
                      ]
                    }
                  },
                  {
                    "type": "input",
                    "options": {
                      "code": "phone",
                      "label": "Номер телефона",
                      "type": "text",
                      "placeholder": [
                        "+79261234567",
                        "+7 (985) 678-90-12",
                        "+7 499 876-54-32",
                        "89112345678"
                      ]
                    }
                  },
                  {
                    "type": "input",
                    "options": {
                      "code": "password",
                      "label": "Пароль",
                      "type": "password",
                      "placeholder": "••••••••"
                    }
                  },
                  {
                    "type": "input",
                    "options": {
                      "code": "repeat_password",
                      "label": "Повтор пароля",
                      "type": "password",
                      "placeholder": "••••••••"
                    }
                  },
                  {
                    "type": "button",
                    "options": {
                      "label": "Регистрация",
                      "css": {
                        "style": {
                          "default": {
                            "background": "#86C685",
                            "color": "white",
                            "font-size": "32px",
                            "margin-bottom": "8px"
                          },
                          "hover": {
                            "background": "#66BB65"
                          },
                          "click": {
                            "background": "#AED4AE"
                          }
                        }
                      },
                    },
                    "events": {
                      "click": {
                        "type": "valid",
                        "options": {
                          "values": [
                            {
                              "code": "fio",
                              "valids": {
                                "len": {
                                  "min": 1,
                                  "max": 50
                                }
                              }
                            },
                            {
                              "code": "email",
                              "valids": {
                                "len": {
                                  "min": 1,
                                  "max": 50
                                }
                              }
                            },
                            {
                              "code": "phone",
                              "valids": {
                                "len": {
                                  "min": 1,
                                  "max": 50
                                }
                              }
                            },
                            {
                              "code": "password",
                              "valids": {
                                "len": {
                                  "min": 8,
                                  "max": 50
                                }
                              }
                            },
                            {
                              "code": "repeat_password",
                              "valids": {
                                "replay": "password"
                              }
                            }
                          ],
                          "success": {
                            "type": "ajax",
                            "options": {
                              "method": "POST",
                              "url": "/api/upform/auth/normal/reg/",
                              "values": {
                                "fio": {
                                  "code": "fio"
                                },
                                "email": {
                                  "code": "email"
                                },
                                "phone": {
                                  "code": "phone"
                                },
                                "login": {
                                  "code": "login"
                                },
                                "password": {
                                  "code": "password"
                                },
                                "repeat_password": {
                                  "code": "repeat_password"
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  },
                  {
                    "type": "text",
                    "options": {
                      "label": "Вход",
                      "css": {
                        "style": {
                          "default": {
                            "color": "#333333",
                            "font-size": "16px",
                            "text-align": "center",
                            "cursor": "pointer",
                            "text-decoration": "underline",
                            "margin-top": "12px"
                          },
                          "hover": {
                            "color": "#4870BF"
                          },
                          "click": {
                            "color": "#4081FF"
                          }
                        }
                      }
                    },
                    "events": {
                      "click": {
                        "type": "form.change",
                        "options": {
                          "type": "login",
                          "tab": ""
                        }
                      }
                    }
                  }
                ]
              }
            }
          },
          "forget_password": {
            "label": "Восстановления пароля",
            "tabs": {
              "stage_1": {
                "show": true,
                "label": "Восстановления пароля",
                "css": {
                  "style": {
                    "default": {
                      "background": "transparent",
                      "transition": "all 0.05s"
                    },
                    "hover": {
                      "background": "#A3DFA2"
                    },
                    "click": {
                      "background": "#87E785"
                    },
                    "class": {
                      "active": {
                        "background": "#86C685"
                      }
                    }
                  }
                },
                "сontrols": [
                  {
                    "type": "text",
                    "options": {
                      "label": "Восстановления пароля",
                      "css": {
                        "style": {
                          "default": {
                            "color": "#000",
                            "font-size": "32px",
                            "text-align": "center",
                            "margin-bottom": "12px"
                          }
                        }
                      }
                    }
                  },
                  {
                    "type": "input",
                    "options": {
                      "code": "email",
                      "label": "Почта",
                      "type": "text",
                      "placeholder": [
                        "johndoe@gmail.com",
                        "sarahsmith@yahoo.com",
                        "michaeldavis@outlook.com",
                        "emilyjones@mail.ru",
                        "alexwilson@yandex.ru"
                      ]
                    }
                  },
                  {
                    "type": "button",
                    "options": {
                      "label": "Отправить",
                      "css": {
                        "style": {
                          "default": {
                            "background": "#86C685",
                            "color": "white",
                            "font-size": "32px",
                            "margin-bottom": "8px"
                          },
                          "hover": {
                            "background": "#66BB65"
                          },
                          "click": {
                            "background": "#AED4AE"
                          }
                        }
                      },
                    },
                    "events": {
                      "click": {
                        "type": "valid",
                        "options": {
                          "values": [
                            {
                              "code": "email",
                              "valids": {
                                "len": {
                                  "min": 1,
                                  "max": 50
                                }
                              }
                            },
                          ],
                          "success": {
                            "type": "ajax",
                            "options": {
                              "method": "POST",
                              "url": "/api/upform/auth/forget_password/",
                              "values": {
                                "email": {
                                  "code": "email"
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  },
                  {
                    "type": "text",
                    "options": {
                      "label": "Вход",
                      "css": {
                        "style": {
                          "default": {
                            "color": "#333333",
                            "font-size": "16px",
                            "text-align": "center",
                            "cursor": "pointer",
                            "text-decoration": "underline",
                            "margin-top": "12px"
                          },
                          "hover": {
                            "color": "#4870BF"
                          },
                          "click": {
                            "color": "#4081FF"
                          }
                        }
                      }
                    },
                    "events": {
                      "click": {
                        "type": "form.change",
                        "options": {
                          "type": "login",
                          "tab": "normal"
                        }
                      }
                    }
                  }
                ]
              },
            }
          },
          "custom": {
            "tabs": {
              "message": {
                "show": true,
                "code": "title",
                "label": "Заголовок таба",
                "css": {
                  "style": {
                    "default": {
                      "background": "transparent",
                      "transition": "all 0.05s"
                    },
                    "hover": {
                      "background": "#af9eff"
                    },
                    "click": {
                      "background": "#5d60ff"
                    },
                    "class": {
                      "active": {
                        "background": "#2264ff"
                      }
                    }
                  }
                },
                "сontrols": [
                  {
                    "type": "text",
                    "code": "title",
                    "options": {
                      "css": {
                        "style": {
                          "default": {
                            "color": "#000",
                            "font-size": "32px",
                            "text-align": "center",
                            "margin-bottom": "12px"
                          }
                        }
                      }
                    }
                  },
                  {
                    "type": "text",
                    "code": "text",
                    "options": {
                      "css": {
                        "style": {
                          "default": {
                            "color": "#333333",
                            "font-size": "20px",
                            "text-align": "center"
                          },
                          "hover": {
                            "color": "#4870BF"
                          },
                          "click": {
                            "color": "#4081FF"
                          }
                        }
                      }
                    }
                  }
                ]
              }
            }
          }
        },
        "values": {
          "phone": "",
          "phone_code": "",
          "code": "",
          "login": "",
          "password": "",
          "repeat_password": "",
          "fio": "",
          "email": ""
        }
      };


      var options = $.extend({}, defaults, params);
      const $upform = this
      const $tabs = $(`<div class="tabs"></div>`)
      const $content = $(`<div class="content"></div>`)

      if (!$upform.data('upform')) {
        options.id = Math.random().toString(36).substring(15)
        $upform.data('upform', options);


        // Основной каркас формы
        $upform.append($tabs, $content)

        $upform.addClass("upform show")

        //hover
        $tabs.on("mouseenter", '.item', function () {
          let type_key = $(this).data("type")
          let tab_key = $(this).data("tab")
          let tab_obj = options.forms[type_key].tabs[tab_key]

          if (tab_obj.css?.style?.hover) {
            $(this).css(tab_obj.css?.style?.hover)
          }
        })
        // Кликнул и не отпрустил
        $tabs.on("mousedown", '.item', function () {
          let type_key = $(this).data("type")
          let tab_key = $(this).data("tab")
          let tab_obj = options.forms[type_key].tabs[tab_key]

          if (tab_obj.css?.style?.click) {
            $(this).css(tab_obj.css?.style?.click)
          }
        })

        // Кликнул и отпустил
        $tabs.on("click", '.item', function () {
          let type_key = $(this).data("type")
          let tab_key = $(this).data("tab")

          options.type = type_key
          options.tab = tab_key
          $upform.data('upform', options);
          $upform.upform('render')
        })

        //Выход за пределы
        $tabs.on("mouseleave", '.item', function () {
          let type_key = $(this).data("type")
          let tab_key = $(this).data("tab")
          let tab_obj = options.forms[type_key].tabs[tab_key]

          if ($(this).hasClass("active")) {
            if (tab_obj.css?.style?.class?.active) {
              $(this).css(tab_obj.css?.style?.class?.active)
            }
          }
          else {
            if (tab_obj.css?.style?.default) {
              $(this).css(tab_obj.css?.style?.default)
            }
          }
        })

        // ======== Кнопки ======== //

        // Навелся на элемент
        $content.on("mouseenter", '.control', function () {
          let type_key = $(this).data("type")
          let tab_key = $(this).data("tab")
          let сontrol_key = parseInt($(this).data("сontrol_key"))

          let control = options.forms[type_key].tabs[tab_key].сontrols[сontrol_key].options
          let css = control?.css

          if (css && css?.style?.hover) {
            $(this).css(css?.style?.hover)
          }
        })

        // Кликнул и отпустил
        $content.on("click", '.control', function () {
          let type_key = $(this).data("type")
          let tab_key = $(this).data("tab")
          let сontrol_key = parseInt($(this).data("сontrol_key"))

          let control = options.forms[type_key].tabs[tab_key].сontrols[сontrol_key].options
          let events = options.forms[type_key].tabs[tab_key].сontrols[сontrol_key].events

          if (events?.click) {
            if (events.click.type == "valid") {
              let valid_result = $upform.upform("event.valid", events.click.options)
              $upform.upform("render.valid", valid_result)
              if (valid_result.valid) {
                if (events.click.options.success.type == "ajax") {
                  $upform.upform("event.ajax", events.click.options.success.options)
                }
              }
            }
            if (events.click.type == "href") {
              $upform.upform("event.href", events.click.options)
            }

            if (events.click.type == "form.change") {
              $upform.upform("form.change", events.click)
            }
          }
        })

        //Выход за пределы
        $content.on("mouseleave", '.control', function () {
          let type_key = $(this).data("type")
          let tab_key = $(this).data("tab")
          let сontrol_key = $(this).data("сontrol_key")

          let control = options.forms[type_key].tabs[tab_key].сontrols[сontrol_key].options
          let css = control?.css

          if (css && css.style?.default) {
            $(this).css(css.style?.default)
          }
        })


        // ======== Inputs ======== //

        // Изменения input
        $content.on("change keyup keydown", '.input', function () {
          let label = $(this).parents(".label")
          let type_key = $(label).data("type")
          let tab_key = $(label).data("tab")
          let сontrol_key = $(label).data("сontrol_key")

          let control = options.forms[type_key].tabs[tab_key].сontrols[сontrol_key].options
          let code = control.code

          let value = $(this).val()
          $(this).val(value)

          options.values[code] = value

          console.log(value)

          $upform.data('upform', options);
        })
      }
      return $upform;
    },
    "render": function () {
      $(this).upform("render.header")
      $(this).upform("render.body")
    },
    "render.header": function () {
      const $upform = this
      let opt = $(this).data('upform');

      const $tabs = $(this).find(".tabs")
      $tabs.empty();


      let type_obj = opt.forms[opt.type]

      for (tab_key in type_obj.tabs) {


        let tab_obj = type_obj.tabs[tab_key]
        let style = tab_obj.css?.style
        if (tab_obj.show) {
          let $el = $(`<div class="item">${tab_obj.label}</div>`)
          if (opt.tab == tab_key)
            $el.addClass("active")

          $el.data("type", opt.type).data("tab", tab_key)


          // Стили табов
          if (style) {
            if (style?.default) {
              $el.css(style?.default)
            }
            if (style?.class) {
              for (style_key in style?.class) {
                if ($el.hasClass(style_key)) {
                  let style_class = style.class?.[style_key]
                  if (style_class) {
                    $el.css(style_class)
                  }
                }
              }
            }
          }

          $tabs.append($el)
        }
      }


    },
    "render.body": function () {
      const $upform = this
      let opt = $(this).data('upform');

      const $content = $(this).find(".content")
      $content.empty();

      let сontrols = opt.forms[opt.type].tabs[opt.tab].сontrols
      for (сontrol_key in сontrols) {
        let control = сontrols[сontrol_key]
        let options = control.options
        let css = options.css?.style?.default
        let $el = null


        if (control.type == "html") {
          $el = $(options.html).addClass("control")
          $el.data("type", opt.type).data("tab", opt.tab).data("сontrol_key", сontrol_key)
          if (css) $el.css(css)
        }


        if (control.type == "text") {
          $el = $(`<span class="control">${options.label}</span>`)
          $el.data("type", opt.type).data("tab", opt.tab).data("сontrol_key", сontrol_key)
          if (css) $el.css(css)
        }


        if (control.type == "button") {
          $el = $(`<button class="button control">${options.label}</button>`)
          $el.data("type", opt.type).data("tab", opt.tab).data("сontrol_key", сontrol_key)
          if (css) $el.css(css)
        }

        if (control.type == "input") {
          placeholder = ""
          if (Array.isArray(options.placeholder)) {
            placeholder = options.placeholder[Math.floor(Math.random() * options.placeholder.length)]
          }
          else {
            placeholder = options.placeholder
          }

          $el = $(`
            <label class="label control" code="${options.code}">
              <span>
                ${options.label}
              </span>
              <input type="${options.type}"
                class="input"
                placeholder="${placeholder}">
              </input>
            </label>
            `
          )
          $el.data("type", opt.type).data("tab", opt.tab).data("сontrol_key", сontrol_key)
          if (css) $el.css(css)
        }


        if ($el)
          $content.append($el)
      }

    },
    "render.valid": function (valids) {
      let opt = $(this).data('upform');

      for (const code in valids.values) {
        let obj = valids.values[code]
        let $label = $(this).find(`.label[code="${code}"]`)
        $label.find("span.error").remove() //Удалить прошлые ошибки
        if (obj.valid) {
          $label.removeClass("error").addClass("success")
        }
        else {
          $label.removeClass("success").addClass("error")
          for (const error of obj.errors) {
            $label.append(`<span class="error">${error}</span>`)
          }
        }
      }
    },
    "event.valid": function (event) {
      let opt = $(this).data('upform');

      let result = {
        "values": {},
        "valid": true
      }
      for (obj of event.values) {
        let rules = obj.valids
        let value = opt.values[obj.code]

        let valid = true
        let errors = []

        if (rules?.len) {
          if (rules?.len?.min && value.length < rules?.len?.min) {
            errors.push(`Количество символов не может быть меньше ${rules?.len?.min}`)
            valid = false
            result["valid"] = false
          }
          if (rules?.len?.max && value.length > rules?.len?.max) {
            errors.push(`Количество символов не может быть больше ${rules?.len?.max}`)
            valid = false
            result["valid"] = false
          }
        }

        if (rules?.re) {
          let isMatch = rules?.re.value.test(value);
          if (!isMatch) {
            errors.push(rules?.re.error)
            valid = false
            result["valid"] = false
          }
        }


        result["values"][obj.code] = {
          "valid": valid,
          "errors": errors,
        }
      }

      return result
    },
    "event.ajax": function (event) {
      let opt = $(this).data('upform');
      let $upform = this

      let param = {}

      for (const key in event.values) {
        const value = event.values[key];
        if (value?.code) {
          param[key] = opt.values[key]
        }
      }


      if (event.method == "POST") {
        $.ajax({
          type: event.method,
          url: event.url,
          data: param,
          beforeSend: function (request) {
            request.setRequestHeader('X-CSRFToken', getCookie('csrftoken'))
          },
          success: function (response) {
            let upform = response?.upform
            let type = upform.type
            if (type.indexOf("form.custom") == 0)
              $($upform).upform("render.form.custom", upform)

            if (type.indexOf("reload") == 0)
              location.reload()

            if (type.indexOf("form.change") == 0)
              $($upform).upform("form.change", upform)

            if (type.indexOf("render.valid") == 0)
              $($upform).upform("render.valid", upform)
          }
        });
      }
      else {
        $.ajax({
          type: event.method,
          url: event.url,
          data: param,
          success: function (response) {
            console.log(response)
          }
        });
      }
    },
    "form.change": function (event) {
      const $upform = this
      let opt = $(this).data('upform');

      if (event.options.type && event.options.type != "")
        opt.type = event.options.type

      if (event.options.tab && event.options.tab != "")
        opt.tab = event.options.tab

      $upform.data('upform', opt);
      $upform.upform('render');
    },
    "render.form.custom": function (custom_options) {
      let opt = $(this).data('upform');

      const $content = $(this).find(".content")
      $content.empty();

      if (custom_options.type == "form.custom.message") {
        let сontrols = opt.forms.custom.tabs.message.сontrols
        for (сontrol_key in сontrols) {
          let control = сontrols[сontrol_key]
          let options = control.options
          let css = options.css?.style?.default
          let $el = null

          let custom_options_сontrols_keys = Object.keys(custom_options.сontrols)

          if (custom_options_сontrols_keys.includes(control.code)) {
            let label = custom_options.сontrols[control.code].label

            if (control.type == "text") {
              $el = $(`<span>${label}</span>`)
              $el.data("type", opt.type).data("tab", tab_key).data("сontrol_key", сontrol_key)
              if (css) $el.css(css)

            }

            if ($el)
              $content.append($el)
          }
        }
      }
      opt.type = "custom"
      opt.tab = custom_options.type
      $(this).data('upform', opt);
    },

    "event.href": function (event) {
      let url = event.url
      if (event.target == "_self" || event.target == "")
        location.href = url

      if (event.target == "_blank")
        window.open(url, "_blank")

      if (event.target == "_parent")
        window.open(url, "_parent")
    }
  }


  $.fn.upform = function (method) {
    if (methods[method]) { return methods[method].apply(this, Array.prototype.slice.call(arguments, 1)) }
    else if (typeof method === 'object' || !method) { return methods.init.apply(this, arguments) }
    else { $.error('Метод "' + method + '" в плагине не найден') }
  };
})
