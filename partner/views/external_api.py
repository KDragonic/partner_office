import datetime
import html
import math
import os
import random
from django.conf import settings
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.templatetags.static import static
from partner.models import *
import datetime
from django.views.decorators.http import require_GET, require_POST
from django.template.loader import render_to_string

