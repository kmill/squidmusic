import iso8601

class ExceptionExpected(Exception):
    """Raise when the exception we expected isn't raised"""

def assert_raises(exception):
    def decorator(fn):
        def new_fn(*args, **kwargs):
            try:
                fn(*args, **kwargs)
            except exception:
                return
            except Exception, e:
                raise ExceptionExpected("Expected exception %r, got exception %s" % (exception, e))
            raise ExceptionExpected("Expected exception %r" % exception)
        new_fn.__doc__ = fn.__doc__
        new_fn.__name__ = fn.__name__
        return new_fn
    return decorator

def test_iso8601_regex():
    assert iso8601.ISO8601_REGEX.match("2006-10-11T00:14:33Z")
    assert iso8601.ISO8601_REGEX.match("2006-01-02T00:04:03Z")

def test_timezone_regex():
    assert iso8601.TIMEZONE_REGEX.match("+01:00")
    assert iso8601.TIMEZONE_REGEX.match("+00:00")
    assert iso8601.TIMEZONE_REGEX.match("+01:20")
    assert iso8601.TIMEZONE_REGEX.match("-01:00")

def test_parse_datetime():
    d = iso8601.parse_datetime("2006-10-20T15:34:56Z")
    assert d.year == 2006
    assert d.month == 10
    assert d.day == 20
    assert d.hour == 15
    assert d.minute == 34
    assert d.second == 56
    assert d.tzinfo == iso8601.UTC

def test_parse_datetime_z():
    d = iso8601.parse_datetime("2006-10-20T15:34:56Z", default_timezone=iso8601.FixedOffset(1, 0, "IST"))
    assert d.tzinfo == iso8601.UTC

def test_parse_datetime_different_timezone():
    tz = iso8601.FixedOffset(1, 0, "IST")
    d = iso8601.parse_datetime("2006-10-20T15:34:56", default_timezone=tz, strict=False)
    assert d.tzinfo == tz

def test_parse_datetime_fraction():
    d = iso8601.parse_datetime("2006-10-20T15:34:56.123Z")
    assert d.year == 2006
    assert d.month == 10
    assert d.day == 20
    assert d.hour == 15
    assert d.minute == 34
    assert d.second == 56
    assert d.microsecond == 123000
    assert d.tzinfo == iso8601.UTC

def test_parse_datetime_fraction_2():
    """From issue 6, allow slightly looser date parsing
    
    """
    d = iso8601.parse_datetime("2007-5-7T11:43:55.328Z'", strict=False)
    assert d.year == 2007
    assert d.month == 5
    assert d.day == 7
    assert d.hour == 11
    assert d.minute == 43
    assert d.second == 55
    assert d.microsecond == 328000
    assert d.tzinfo == iso8601.UTC

@assert_raises(iso8601.ParseError)
def test_parse_issue_6_strict():
    iso8601.parse_datetime("2007-5-7T11:43:55.328Z'")

def test_parse_datetime_tz():
    d = iso8601.parse_datetime("2006-10-20T15:34:56.123+02:30")
    assert d.year == 2006
    assert d.month == 10
    assert d.day == 20
    assert d.hour == 15
    assert d.minute == 34
    assert d.second == 56
    assert d.microsecond == 123000
    assert d.tzinfo.tzname(None) == "+02:30"
    offset = d.tzinfo.utcoffset(None)
    assert offset.days == 0
    assert offset.seconds == 60 * 60 * 2.5

@assert_raises(iso8601.ParseError)
def test_parse_invalid_datetime():
    iso8601.parse_datetime(None)

@assert_raises(iso8601.ParseError)
def test_parse_invalid_datetime2():
    iso8601.parse_datetime("23")

def test_parse_no_timezone_no_strict():
    """issue 4 - Handle datetime string without timezone
    
    This tests what happens when you parse a date with no timezone. While not
    strictly correct this is quite common. I'll assume UTC for the time zone
    in this case.
    """
    d = iso8601.parse_datetime("2007-01-01T08:00:00", strict=False)
    assert d.year == 2007
    assert d.month == 1
    assert d.day == 1
    assert d.hour == 8
    assert d.minute == 0
    assert d.second == 0
    assert d.microsecond == 0
    assert d.tzinfo == iso8601.UTC


@assert_raises(iso8601.ParseError)
def test_parse_no_timezine_strict():
    """Variation of issue 4, raise a ParseError when there is no time zone
    
    """
    iso8601.parse_datetime("2007-01-01T08:00:00")

@assert_raises(iso8601.ParseError)
def test_parse_incorrect_date_digits():
    iso8601.parse_datetime("2007-1-1T08:00:00Z")

def test_space_separator():
    """Handle a separator other than T
    
    """
    d = iso8601.parse_datetime("2007-06-23 06:40:34.00Z")
    assert d.year == 2007
    assert d.month == 6
    assert d.day == 23
    assert d.hour == 6
    assert d.minute == 40
    assert d.second == 34
    assert d.microsecond == 0
    assert d.tzinfo == iso8601.UTC
