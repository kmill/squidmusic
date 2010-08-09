from django import template

register = template.Library()

def msec_to_string(value) :
    value = int(value)//1000
    h = value // 3600
    value -= 3600 * h
    m = value // 60
    value -= 60 * m
    s = ""
    if h > 0 :
        s = str(h) + ":"
        if m < 10 :
            s += "0"
        s += str(m) + ":"
        if value < 10 :
            s += "0"
        s += str(value)
    else :
        s += str(m) + ":"
        if value < 10 :
            s += "0"
        s += str(value)
    return s

register.filter('msec_to_string', msec_to_string)
